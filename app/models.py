from google.appengine.ext import ndb
import datetime
import re


class Model(ndb.Model):
  modified = ndb.DateTimeProperty()
  resource_id = ndb.StringProperty()
  slug = ndb.ComputedProperty(lambda self: self.generate_slug(self.title))
  title = ndb.StringProperty()
  weight = ndb.FloatProperty(default=0.0)
  synced = ndb.DateTimeProperty()

  def __getattr__(self, name):
    # Allow dynamic lookups of references. For example, an entity with
    # a property `category_key` will return the corresponding category
    # when accessing `entity.category`.
    reference_key_name = '{}_key'.format(name)
    if hasattr(self, reference_key_name):
      key = getattr(self, reference_key_name)
      return key.get() if key is not None else None
    return self.__getattribute__(name)

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

  @classmethod
  def parse_title_and_weight(cls, unprocessed_title):
    match = re.findall('\[([^\]]*)\] (.*)', unprocessed_title)
    if match:
      try:
        return (match[0][1], float(match[0][0]))
      except ValueError:
        return (match[0][1], None)
    return (unprocessed_title, None)

  @property
  def ident(self):
    return self.key.urlsafe()

  @classmethod
  def get_by_ident(cls, ident):
    key = ndb.Key(urlsafe=ident)
    return key.get()
