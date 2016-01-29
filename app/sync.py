from . import assets
from . import folders
from . import pages
from google.appengine.api import channel
from google.appengine.api import memcache
from googleapiclient import discovery
from googleapiclient import errors
from oauth2client import appengine
from oauth2client import client
import appengine_config
import httplib2
import json
import logging
import os


CONFIG = appengine_config.CONFIG

SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
]


def get_credentials():
  if os.getenv('TESTING'):
    path = os.path.join(appengine_config.CONFIG_PATH, CONFIG['key'])
    credentials = client.SignedJwtAssertionCredentials(
        CONFIG['service_account'],
        open(path).read(),
        scope=SCOPE,
    )
  else:
    credentials = appengine.AppAssertionCredentials(SCOPE)
  return credentials


http = httplib2.Http(memcache)
credentials = get_credentials()
credentials.authorize(http)
service = discovery.build('drive', 'v2', http=http)


def get_service():
  return service


def update_channel(user, message):
  if user:
    content = json.dumps({'message': message})
    channel.send_message(user.ident, content)
  logging.info(message)


def download_folder(resource_id):
  service = get_service()
  page_token = None
  child_resource_responses = []
  while True:
    params = {}
    if page_token:
      params['pageToken'] = page_token
    children = service.children().list(
        folderId=resource_id, **params).execute()
    for child in children.get('items', []):
      child_resource_responses.append(child)
    page_token = children.get('nextPageToken')
    if not page_token:
      break
  return child_resource_responses


def is_assets_folder(resp):
  return 'assets' in resp['title'].lower().strip()


def download_resource(resource_id, user=None):
  service = get_service()
  resp = service.files().get(fileId=resource_id).execute()
  if resp['mimeType'] == 'application/vnd.google-apps.folder':
    if is_assets_folder(resp):
      text = 'Processing assets: {} ({})'
      message = text.format(resp['title'], resource_id)
      update_channel(user, message)
      process_assets_folder_response(resp, user)
    else:
      text = 'Processing folder: {} ({})'
      message = text.format(resp['title'], resource_id)
      update_channel(user, message)
      process_folder_response(resp, user)
  else:
    text = 'Processing file: {} ({})'
    message = text.format(resp['title'], resource_id)
    update_channel(user, message)
    process_file_response(resp)


def process_assets_folder_response(resp, user):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  child_resource_ids = [child['id'] for child in child_resource_responses]
  set_resources_public(child_resource_ids)
  for child in child_resource_responses:
    download_resource(child['id'], user)


def process_folder_response(resp, user):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  for child in child_resource_responses:
    download_resource(child['id'], user)


def get_file_content(resp):
  service = get_service()
  for mimetype, url in resp['exportLinks'].iteritems():
    if mimetype.endswith('html'):
      resp, content = service._http.request(url)
      if resp.status != 200:
        raise Exception()
      return content


def process_file_response(resp):
  if resp['mimeType'] == 'application/vnd.google-apps.document':
    page = pages.Page.process(resp)
    if page.should_process_content(resp):
      unprocessed_content = get_file_content(resp)
      page.process_content(unprocessed_content)
  else:
    assets.Asset.process(resp)


def set_resources_public(resource_ids):
  service = get_service()
  batch = service.new_batch_http_request()
  permission = {
      'value': None,
      'type': 'anyone',
      'role': 'reader',
  }
  for resource_id in resource_ids:
    req = service.permissions().insert(
        fileId=resource_id,
        body=permission)
    batch.add(req)
  batch.execute()
