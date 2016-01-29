import webapp2
import yaml
from google.appengine.ext import ndb


class Settings(ndb.Model):
  content = ndb.TextProperty()

  @classmethod
  def singleton(cls):
    key = ndb.Key(cls.__name__, 'settings')
    ent = key.get()
    if ent is None:
      ent = cls(key=key)
      ent.put()
    return ent

  @property
  def fields(self):
    return yaml.loads(self.content)
