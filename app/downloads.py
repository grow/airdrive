from . import models
from google.appengine.ext import ndb


class Download(models.Model):
  asset_key = ndb.KeyProperty()
  downloaded = ndb.DateTimeProperty(auto_now_add=True)
  downloaded_by_key = ndb.KeyProperty()
