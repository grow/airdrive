from google.appengine.ext import ndb
import datetime
import re


class Model(ndb.Model):

  def __getattr__(self, name):
    # Allow dynamic lookups of references. For example, an entity with
    # a property `category_key` will return the corresponding category
    # when accessing `entity.category`.
    reference_key_name = '{}_key'.format(name)
    if hasattr(self, reference_key_name) and not name in self.__dict__:
      key = getattr(self, reference_key_name)
      return key.get() if key is not None else None
    return self.__getattribute__(name)

  @classmethod
  def get(cls, ident):
    key = ndb.Key(cls.__name__, ident)
    ent = key.get()
    return ent

  @classmethod
  def get_or_instantiate(cls, ident):
    ent = cls.get(ident)
    if ent is None:
      key = ndb.Key(cls.__name__, ident)
      ent = cls(key=key)
    return ent

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
  def update_multi(cls, messages):
    ents = cls.get_multi(messages)
    for i, ent in enumerate(ents):
      ent.update(messages[i])
    return ents

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


class BaseResourceModel(Model):
  modified = ndb.DateTimeProperty()
  resource_id = ndb.StringProperty()
  slug = ndb.ComputedProperty(lambda self: self.generate_slug(self.title))
  title = ndb.StringProperty()
  weight = ndb.FloatProperty(default=0.0)
  synced = ndb.DateTimeProperty()
  draft = ndb.BooleanProperty()
  hidden = ndb.BooleanProperty()
  color = ndb.StringProperty()
  interstitial = ndb.BooleanProperty()
  internal = ndb.BooleanProperty()
  template = ndb.StringProperty()
  is_parent = ndb.BooleanProperty()
  is_asset_container = ndb.BooleanProperty()
  title_lower = ndb.StringProperty()
  top = ndb.BooleanProperty()
  linkcolor = ndb.StringProperty()
  publicname = ndb.StringProperty()

  @property
  def resource_type(self):
    return self.__class__.__name__

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
    draft = '[draft]' in title.lower()
    hidden = '[hidden]' in title.lower()
    weight = float(order_matches[0]) if order_matches else None
    template_matches = re.findall('\[template\|([^\]]*)\]', title.lower())
    template = template_matches[0] if template_matches else None
    color_matches = re.findall('\[color\|([^\]]*)\]', title.lower())
    color = color_matches[0] if color_matches else None
    linkcolor_matches = re.findall('\[linkcolor\|([^\]]*)\]', title.lower())
    linkcolor = linkcolor_matches[0] if linkcolor_matches else None
    publicname = re.findall('\[publicname\|([^\]]*)\]', title)
    publicname = template_matches[0] if template_matches else None
    internal = '[internal]' in title.lower()
    is_parent = '[parent]' in title.lower()
    is_top = '[top]' in title.lower()
    is_asset_container = '[assets]' in title.lower()
    cleaned_title = re.sub('\[[^\]]*\]', '', title).strip()
    title_lower = cleaned_title.lower()
    return (cleaned_title, weight, draft, hidden, color, internal, template, is_parent, is_asset_container, title_lower, is_top, linkcolor, publicname)

  def parse_title(self, unprocessed_title):
    self.title, self.weight, self.draft, self.hidden, self.color, self.internal, self.template, self.is_parent, self.is_asset_container, self.title_lower, self.top, self.linkcolor, self.publicname = (
        self._parse_title(unprocessed_title))
