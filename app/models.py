from google.appengine.ext import ndb
import re


class Model(ndb.Model):

  @classmethod
  def get(cls, ident):
    key = ndb.Key(cls.__name__, ident)
    return key.get()

  @classmethod
  def get_or_instantiate(cls, ident):
    ent = cls.get(ident)
    if ent is None:
      key = ndb.Key(cls.__name__, ident)
      ent = cls(key=key)
    return ent

  @classmethod
  def generate_parent_keys(cls, parents_resp):
    return [
        ndb.Key('Folder', parent['id'])
        for parent in parents_resp]

  @classmethod
  def generate_slug(cls, text):
    if text is not None:
      return re.sub(r'\W+', '-', text.lower())
