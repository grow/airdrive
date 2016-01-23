from . import models
from google.appengine.ext import ndb
import appengine_config
import datetime
import os

DOWNLOAD_URL_FORMAT = 'https://www.googleapis.com/drive/v3/files/{resource_id}?alt=media&key={key}'

CONFIG = appengine_config.CONFIG


class Asset(models.Model):
  resource_id = ndb.StringProperty()
  title = ndb.StringProperty()
  synced = ndb.DateTimeProperty()
  size = ndb.IntegerProperty()
  build = ndb.IntegerProperty()
  mimetype = ndb.StringProperty()
  thumbnail_url = ndb.StringProperty()
  md5 = ndb.StringProperty()
  parents = ndb.KeyProperty(repeated=True)
  slug = ndb.ComputedProperty(lambda self: self.generate_slug(self.title))
  basename = ndb.StringProperty()
  ext = ndb.StringProperty()
  modified = ndb.DateTimeProperty()
  url = ndb.StringProperty()
  icon_url = ndb.StringProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.mimetype = resp['mimeType']
    ent.size = int(resp['fileSize'])
    ent.url = resp['webContentLink']
    ent.icon_url = resp['iconLink']
    ent.thumbnail_url = resp['thumbnailLink']
    ent.title = resp['title']
    ent.md5 = resp['md5Checksum']
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.basename, ent.ext = os.path.splitext(resp['title'])
    ent.put()

  @property
  def media_url(self):
    return DOWNLOAD_URL_FORMAT.format(
        resource_id=self.resource_id,
        key=CONFIG['apikey'])
