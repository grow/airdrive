from . import assets
from . import folders
from . import models
from . import pages
from . import settings
from google.appengine.api import app_identity
from google.appengine.api import channel
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from google.appengine.ext import deferred
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
from oauth2client import appengine
from oauth2client import client
import appengine_config
import cStringIO
import cloudstorage as gcs
import httplib
import httplib2
import json
import logging
import os
import time

BUCKET = app_identity.get_default_gcs_bucket_name()

CONFIG = appengine_config.CONFIG

SCOPE = [
    'https://www.googleapis.com/auth/devstorage.full_control',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/userinfo.email',
]

CHUNKSIZE = 10 * 1024 * 1024  # 20 MB per request.
GCS_UPLOAD_CHUNKSIZE = 10 * 1024 * 1024
NUM_RETRIES = 2
BACKOFF = 4  # Seconds.

# KeyError: 'range'
# lib/googleapiclient/http.py", line 902, in _process_response
# self.resumable_progress = int(resp['range'].split('-')[1]) + 1
ERRORS_TO_RETRY = (IOError, httplib2.HttpLib2Error, urlfetch_errors.DeadlineExceededError, KeyError)


class Error(Exception):
  pass


class UploadRequiredError(Error):
  pass


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
  service_http = httplib2.Http()
  credentials = get_credentials()
  credentials.authorize(service_http)
  service = discovery.build('drive', 'v2', http=service_http)



def get_service():
  global service
  return service


def get_drive3_service():
  http = httplib2.Http()
  credentials = get_credentials()
  credentials.authorize(http)
  return discovery.build('drive', 'v3', http=http)


def get_storage_service():
  http = httplib2.Http()
  credentials = get_credentials()
  credentials.authorize(http)
  return discovery.build('storage', 'v1', http=http)


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
  items_to_check = current_children['items'] + current_children['assets']
  for child_ent in items_to_check:
    if child_ent.resource_id not in final_children_ids:
      resources_to_delete.append(child_ent)
  if resources_to_delete:
    logging.info('Deleting: {}'.format(resources_to_delete))
    models.Model.delete_multi(resources_to_delete)
  return child_resource_responses


def download_resource(resource_id, user=None, create_channel=False, queue='sync'):
  service = get_service()
  resp = service.files().get(fileId=resource_id).execute()
  if 'mimeType' not in resp:
    logging.error('Received {}'.format(resp))
    return
  title = resp['title']
  if isinstance(title, unicode):
    title = title.encode('utf-8')
  if resp.get('mimeType', '') == 'application/vnd.google-apps.folder':
    text = 'Processing folder: {} ({})'
    message = text.format(title, resource_id)
    update_channel(user, message)
    process_folder_response(resp, user, queue=queue)
  else:
    text = 'Processing file: {} ({})'
    message = text.format(title, resource_id)
    update_channel(user, message)
    process_file_response(resp)
  folders.create_nav()
  if create_channel:
    token = channel.create_channel(user.ident)
    return token


def process_folder_response(resp, user, queue='sync'):
  folders.Folder.process(resp)
  resource_id = resp['id']
  child_resource_responses = download_folder(resp['id'])
  for child in child_resource_responses:
    deferred.defer(download_resource, child['id'], user, queue=queue, _queue=queue)


def get_file_content(resp):
  service = get_service()
  for mimetype, url in resp['exportLinks'].iteritems():
    if mimetype.endswith('html'):
      resp, content = service._http.request(url)
      if resp.status != 200:
        raise Exception()
      return content


def replicate_asset_to_gcs(resp):
  root_folder_id = get_root_folder_id()
  content_type = resp['mimeType']
  thumbnail_bucket_path = None

  # Download thumbnail.
  if 'thumbnailLink' in resp:
    title_slug = models.BaseResourceModel.generate_slug(resp['title'])
    thumbnail_path = 'assets/{}/thumbnail-{}-{}'.format(
        root_folder_id, resp['id'], title_slug)
    thumbnail_bucket_path = '/{}/{}'.format(BUCKET, thumbnail_path)
    if not appengine_config.DEV_SERVER:
      try:
        gcs.stat(thumbnail_bucket_path)
      except gcs.NotFoundError:
        urlfetch_resp = urlfetch.fetch(resp['thumbnailLink'], deadline=60)
        thumbnail_content_type = urlfetch_resp.headers['Content-Type']
        if urlfetch_resp.status_code != 200:
          logging.error('Received {}: {}'.format(
              urlfetch_resp.status_code, resp['thumbnailLink'],
              urlfetch_resp.content))
          raise
        thumbnail_content = urlfetch_resp.content
        logging.info('Wrote: {}'.format(thumbnail_path))
        fp = gcs.open(thumbnail_bucket_path, 'w', thumbnail_content_type)
        fp.write(thumbnail_content)
        fp.close()

  # Download asset.
  title_slug = models.BaseResourceModel.generate_slug(resp['title'])
  path = 'assets/{}/asset-{}-{}'
  path = path.format(root_folder_id, resp['id'], title_slug)
  bucket_path = '/{}/{}'.format(BUCKET, path)
  if not appengine_config.DEV_SERVER:
    try:
      stat = gcs.stat(bucket_path)
      if stat.etag != resp['etag']:
        raise UploadRequiredError()
      raise UploadRequiredError()
    except (gcs.NotFoundError, UploadRequiredError):
      fp = download_asset_in_parts(service, resp['id'])
      write_gcs_file(path, BUCKET, fp, resp['mimeType'])
  return bucket_path, thumbnail_bucket_path


def download_asset_in_parts(service, file_id):
  drive3 = get_drive3_service()
  fp = cStringIO.StringIO()
  request = drive3.files().get_media(fileId=file_id)
  req = http.MediaIoBaseDownload(fp, request, chunksize=CHUNKSIZE)
  done = False
  connections = 0
  while done is False:
    try:
      status, done = req.next_chunk()
      backoff = BACKOFF
      connections += 1
      continue
    except ERRORS_TO_RETRY as e:
      logging.warn('Drive download encountered error to retry: %s' % e)
    retries += 1
    if retries > NUM_RETRIES:
        raise ValueError('Hit max retry attempts with error: %s' % e)
    time.sleep(backoff)
    backoff *= 2
  fp.seek(0)
  logging.info('Downloaded in %s tries: %s', connections, file_id)
  return fp


def write_gcs_file(path, bucket, fp, mimetype):
  storage_service = get_storage_service()
  media = http.MediaIoBaseUpload(
      fp, mimetype=mimetype, chunksize=GCS_UPLOAD_CHUNKSIZE, resumable=True)
  req = storage_service.objects().insert(
      media_body=media, name=path, bucket=bucket)
  resp = None
  backoff = BACKOFF
  retries = 0
  connections = 0
  while resp is None:
    try:
      _, resp = req.next_chunk()
      backoff = BACKOFF  # Reset backoff.
      connections += 1
      continue
    except ERRORS_TO_RETRY as e:
      logging.warn('GCS upload encountered error to retry: %s' % e)
    retries += 1
    if retries > NUM_RETRIES:
        raise ValueError('Hit max retry attempts with error: %s' % e)
    time.sleep(backoff)
    backoff *= 2
  logging.info('Uploaded in %s tries: %s' % (connections, path))


def process_file_response(resp):
  if resp['mimeType'] == 'application/vnd.google-apps.document':
    page = pages.Page.process(resp)
    if page.should_process_content(resp):
      unprocessed_content = get_file_content(resp)
      page.process_content(unprocessed_content)
  else:
    try:
        gcs_path, gcs_thumbnail_path = replicate_asset_to_gcs(resp)
    except:
        text = 'Error replicating asset to GCS: {}'
        logging.error(text.format(resp['title']))
        raise
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
  logging.info('Created root folder: {}'.format(file_id))
  return file_id


def share_root_folder(emails):
  file_id = get_root_folder_id()
  for email in emails:
    permission = {
        'type': 'user',
        'role': 'writer',
        'value': email,
    }
    service.permissions().insert(
        fileId=file_id,
        body=permission,
        fields='id',
    ).execute()
    logging.info('Shared root folder with -> {}'.format(email))


def get_root_folder_id():
  if 'folder' in CONFIG:
    return CONFIG['folder']
  settings_obj = settings.Settings.singleton()
  if settings_obj.form.root_folder_id:
    return settings_obj.form.root_folder_id
  file_id = create_root_folder()
  settings_obj.form.root_folder_id = file_id
  settings_obj.put()
  return file_id
