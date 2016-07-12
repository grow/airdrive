from . import models
from google.appengine.ext import ndb


class Domain(models.Model):
  domain = ndb.StringProperty()
