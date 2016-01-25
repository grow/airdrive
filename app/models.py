from google.appengine.ext import ndb
import datetime
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

  @classmethod
  def parse_datetime_string(cls, datetime_string):
    fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
    return datetime.datetime.strptime(datetime_string, fmt)

  @classmethod
  def get_by_slug(cls, slug, parent=None):
    query = cls.query()
    query = query.filter(cls.slug == slug)
    if parent:
      query = query.filter(cls.parents == ndb.Key('Folder', parent))
    return query.get()
