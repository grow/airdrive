from . import assets
from . import models
from . import pages
from google.appengine.ext import ndb
import datetime
import webapp2


class Folder(models.Model):
  resource_id = ndb.StringProperty()
  updated = ndb.DateTimeProperty(auto_now=True)
  title = ndb.StringProperty()
  synced = ndb.DateTimeProperty()
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  slug = ndb.ComputedProperty(lambda self: self.generate_slug(self.title))
  modified = ndb.DateTimeProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    title = resp['title']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.title = title
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.put()

  @classmethod
  def list(self, parent=None):
    query = Folder.query()
    if parent:
      parent_key = ndb.Key('Folder', parent)
      query = query.filter(Folder.parents == parent_key)
    return query.fetch()

  def list_children(self):
    children = {
        'assets': [],
        'folders': [],
        'pages': [],
    }
    query = assets.Asset.query()
    query = query.filter(assets.Asset.parents == self.key)
    children['assets'] = query.fetch()
    query = pages.Page.query()
    query = query.filter(pages.Page.parents == self.key)
    children['pages'] = query.fetch()
    query = Folder.query()
    query = query.filter(Folder.parents == self.key)
    children['folders'] = query.fetch()
    return children

  @property
  def children(self):
    return self.list_children()

  @webapp2.cached_property
  def parent(self):
    return self.parents[0].get()

  @property
  def url(self):
    return '/{}/folders/{}/'.format(self.parent.slug, self.key.id())
