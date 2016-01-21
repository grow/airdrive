from google.appengine.ext import ndb
from . import models
import datetime


class Asset(models.Model):
  resource_id = ndb.StringProperty()
  title = ndb.StringProperty()
  synced = ndb.DateTimeProperty()
  url = ndb.StringProperty()
  size = ndb.IntegerProperty()
  build = ndb.IntegerProperty()
  mimetype = ndb.StringProperty()
  thumbnail_url = ndb.StringProperty()
  md5 = ndb.StringProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    asset = cls.get_or_instantiate(resource_id)
    asset.mimetype = resp['mimeType']
    asset.size = int(resp['fileSize'])
    asset.thumbnail_url = resp['thumbnailLink']
    asset.title = resp['title']
    asset.url = resp['downloadUrl']
    asset.md5 = resp['md5Checksum']
    asset.synced = datetime.datetime.now()
    asset.put()
