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
  parents = ndb.KeyProperty(repeated=True)
  slug = ndb.StringProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.mimetype = resp['mimeType']
    ent.size = int(resp['fileSize'])
    ent.thumbnail_url = resp['thumbnailLink']
    ent.title = resp['title']
    ent.url = resp['downloadUrl']
    ent.md5 = resp['md5Checksum']
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.put()
