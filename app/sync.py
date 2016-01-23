import appengine_config
from googleapiclient import discovery
from googleapiclient import errors
from oauth2client import appengine
from oauth2client import client
import httplib2
import logging
import os
from . import assets
from . import folders
from . import pages


CONFIG = appengine_config.CONFIG

SERVICE = None

SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
]


def get_credentials():
  if os.getenv('TESTING'):
    credentials = client.SignedJwtAssertionCredentials(
        CONFIG['service_account'],
        open(CONFIG['key']).read(),
        scope=SCOPE,
    )
  else:
    credentials = appengine.AppAssertionCredentials(SCOPE)
  return credentials


def get_service():
  global SERVICE
  if SERVICE is None:
    credentials = get_credentials()
    http = httplib2.Http()
    http = credentials.authorize(http)
    SERVICE = discovery.build('drive', 'v2', http=http)
  return SERVICE


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


def download_resource(resource_id):
  service = get_service()
  resp = service.files().get(fileId=resource_id).execute()
  if resp['mimeType'] == 'application/vnd.google-apps.folder':
    if is_assets_folder(resp):
      text = 'Processing assets: {} ({})'
      logging.info(text.format(resp['title'], resource_id))
      process_assets_folder_response(resp)
    else:
      text = 'Processing folder: {} ({})'
      logging.info(text.format(resp['title'], resource_id))
      process_folder_response(resp)
  else:
    text = 'Processing file: {} ({})'
    logging.info(text.format(resp['title'], resource_id))
    process_file_response(resp)


def process_assets_folder_response(resp):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  child_resource_ids = [child['id'] for child in child_resource_responses]
  set_resources_public(child_resource_ids)
  for child in child_resource_responses:
    download_resource(child['id'])


def process_folder_response(resp):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  for child in child_resource_responses:
    download_resource(child['id'])


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
    if pages.Page.should_reprocess(resp):
      content = get_file_content(resp)
      pages.Page.process(resp, content)
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
