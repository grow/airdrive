from . import assets
from . import folders
from . import models
from . import pages
from google.appengine.api import urlfetch
from google.appengine.api import channel
from google.appengine.api import memcache
from google.appengine.ext import deferred
from google.appengine.api import app_identity
from googleapiclient import discovery
from googleapiclient import errors
from oauth2client import appengine
from oauth2client import client
import appengine_config
import cloudstorage as gcs
import httplib2
import json
import logging
import os

BUCKET = app_identity.get_default_gcs_bucket_name()

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


if appengine_config.OFFLINE:
  service = None
else:
  http = httplib2.Http()
  credentials = get_credentials()
  credentials.authorize(http)
  service = discovery.build('drive', 'v2', http=http)


def get_service():
  global service
  return service


def update_channel(user, message):
  if user:
    content = json.dumps({'message': message})
    channel.send_message(user.ident, content)
  logging.info(message)


def download_folder(resource_id, process_deletes=True):
  service = get_service()
  page_token = None
  child_resource_responses = []
  current_folder = folders.Folder.get(resource_id)
  current_children = []
  if current_folder:
    current_children = current_folder.list_children()
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
  final_children = child_resource_responses
  final_children_ids = [child['id'] for child in child_resource_responses]
  resources_to_delete = []
  for child_ent in current_children['items']:
    if child_ent.resource_id not in final_children_ids:
      resources_to_delete.append(child_ent)
  if resources_to_delete:
    logging.info('Deleting: {}'.format(resources_to_delete))
    models.Model.delete_multi(resources_to_delete)
  return child_resource_responses


def is_assets_folder(resp):
  return 'assets' in resp['title'].lower().strip()


def download_resource(resource_id, user=None, create_channel=False):
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
  folders.create_nav()
  if create_channel:
    token = channel.create_channel(user.ident)
    return token


def process_assets_folder_response(resp, user):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  child_resource_ids = [child['id'] for child in child_resource_responses]
  set_resources_public(child_resource_ids)
  for child in child_resource_responses:
    download_resource(child['id'], user)
    deferred.defer(download_resource, child['id'], user)


def process_folder_response(resp, user):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  for child in child_resource_responses:
    deferred.defer(download_resource, child['id'], user)


def get_file_content(resp):
  service = get_service()
  for mimetype, url in resp['exportLinks'].iteritems():
    if mimetype.endswith('html'):
      resp, content = service._http.request(url)
      if resp.status != 200:
        raise Exception()
      return content


def replicate_asset_to_gcs(resp):
  content_type = resp['mimeType']

  # Download thumbnail.
  if 'thumbnailLink' in resp:
    urlfetch_resp = urlfetch.fetch(resp['thumbnailLink'], deadline=60)
    thumbnail_content_type = urlfetch_resp.headers['Content-Type']
    if urlfetch_resp.status_code != 200:
      logging.error('Received {}: {}'.format(
          urlfetch_resp.status_code, resp['thumbnailLink'],
          urlfetch_resp.content))
      raise
    thumbnail_content = urlfetch_resp.content
    thumbnail_path = 'assets/{}/thumbnail-{}-{}'.format(CONFIG['folder'], resp['id'], resp['title'])
    thumbnail_bucket_path = '/{}/{}'.format(BUCKET, thumbnail_path)
    logging.info('Wrote: {}'.format(thumbnail_path))
    fp = gcs.open(thumbnail_bucket_path, 'w', thumbnail_content_type)
    fp.write(thumbnail_content)
    fp.close()

  # Download asset.
  service = get_service()
  download_resp, content = service._http.request(resp['downloadUrl'])
  if download_resp.status != 200:
    logging.error('Received {} from {}: {}'.format(
        download_resp.status, resp['downloadUrl'],
        content))
    raise
  path = 'assets/{}/asset-{}-{}'.format(CONFIG['folder'], resp['id'], resp['title'])
  bucket_path = '/{}/{}'.format(BUCKET, path)
  fp = gcs.open(bucket_path, 'w', content_type)
  fp.write(content)
  fp.close()
  return bucket_path, thumbnail_bucket_path


def ensure_asset_is_public(resp):
  owned_by_app = False
  for owner in resp['owners']:
    if owner['emailAddress'] == CONFIG['service_account']:
      owned_by_app = True
  if owned_by_app:
    return resp
  service = get_service()
  copied_file = {
      'parents': resp['parents'],
      'title': resp['title']
  }
  new_resp = service.files().copy(
      fileId=resp['id'],
      body=copied_file).execute()
  service.files().trash(fileId=resp['id']).execute()
  logging.info('Duplicated: {}'.format(resp['title']))
  return new_resp



def process_file_response(resp):
  if resp['mimeType'] == 'application/vnd.google-apps.document':
    page = pages.Page.process(resp)
    if page.should_process_content(resp):
      unprocessed_content = get_file_content(resp)
      page.process_content(unprocessed_content)
  else:
    gcs_path, gcs_thumbnail_path = replicate_asset_to_gcs(resp)
    assets.Asset.process(resp, gcs_path=gcs_path,
                         gcs_thumbnail_path=gcs_thumbnail_path)


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


def create_root_folder():
  service = get_service()
  data = {
    'name' : 'Root Folder',
    'mimeType' : 'application/vnd.google-apps.folder'
  }
  resp = service.files().insert(body=data, fields='id').execute()
  file_id = resp['id']
  permission = {
      'type': 'user',
      'role': 'writer',
      'value': 'jeremydw@google.com'
  }
  service.permissions().insert(
      fileId=file_id,
      body=permission,
      fields='id',
  ).execute()
