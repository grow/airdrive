from google.appengine.ext import ndb
from . import models


class Folder(models.Model):
  resource_id = ndb.StringProperty()
  updated = ndb.DateTimeProperty(auto_now=True)
  title = ndb.StringProperty()
  synced = ndb.DateTimeProperty()
  build = ndb.IntegerProperty()
