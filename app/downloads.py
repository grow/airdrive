from . import models
from google.appengine.ext import ndb


class Download(ndb.Model):
  asset_key = ndb.KeyProperty()
  downloaded = ndb.DateTimeProperty(auto_now_add=True)
  downloaded_by_key = ndb.KeyProperty()

  @classmethod
  def create(cls, user, asset):
    ent = cls(
        downloaded_by_key=user.key,
        asset_key=asset.key)
    ent.put()
    asset.num_downloads += 1
    asset.put()

  @classmethod
  def count(cls, user=None, asset=None):
    query = cls.query()
    if user:
      query = query.filter(cls.downloaded_by_key == user.key)
    if asset:
      query = query.filter(cls.asset_key == asset.key)
    return query.count()
