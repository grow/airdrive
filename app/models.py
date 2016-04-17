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
  draft = ndb.BooleanProperty()
  hidden = ndb.BooleanProperty()
  color = ndb.StringProperty()

  @property
  def resource_type(self):
    return self.__class__.__name__

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
  def _parse_title(cls, unprocessed_title):
    title = unprocessed_title
    order_matches = re.findall('^\[([-+]?\d*\.?\d+?|\d+?)\]', unprocessed_title)
    draft = '[draft]' in title
    hidden = '[hidden]' in title
    weight = float(order_matches[0]) if order_matches else None
    color_matches = re.findall('\[color\|([^\]]*)\]', title)
    color = color_matches[0] if color_matches else None
    title = re.sub('\[[^\]]*\]', '', title).strip()
    return (title, weight, draft, hidden, color)

  def parse_title(self, unprocessed_title):
    self.title, self.weight, self.draft, self.hidden, self.color = self._parse_title(unprocessed_title)

  @property
  def ident(self):
    return self.key.urlsafe()

  @classmethod
  def get_by_ident(cls, ident):
    key = ndb.Key(urlsafe=ident)
    return key.get()

  def delete(self):
    self.key.delete()

  @classmethod
  def delete_multi(cls, ents):
    return ndb.Key.delete_multi([ent.key for ent in ents])

  @classmethod
  def get_multi(cls, messages):
    keys = [ndb.Key(urlsafe=message.ident) for message in messages]
    ents = ndb.get_multi(keys)
    return [ent for ent in ents if ent is not None]

  @classmethod
  def to_message_multi(cls, ents, *args, **kwargs):
    return [ent.to_message(*args, **kwargs) for ent in ents if ent is not None]

  @classmethod
  def delete_multi(self, messages):
    keys = [ndb.Key(urlsafe=message.ident) for message in messages]
    return ndb.delete_multi(keys)

  @classmethod
  def search(cls, message=None):
    query = cls.query()
    return query.fetch()
