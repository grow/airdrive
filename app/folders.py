from . import assets
from . import models
from . import pages
from google.appengine.ext import ndb
import datetime
import webapp2

EDIT_URL_FORMAT = "https://drive.google.com/drive/folders/{resource_id}"


class Folder(models.Model):
  updated = ndb.DateTimeProperty(auto_now=True)
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.title, ent.weight = cls.parse_title_and_weight(resp['title'])
    ent.put()

  @classmethod
  def list(self, parent=None):
    query = Folder.query()
    if parent:
      parent_key = ndb.Key('Folder', parent)
      query = query.filter(Folder.parents == parent_key)
      query = query.order(Folder.weight)
    return query.fetch()

  def list_children(self):
    children = {
        'assets': [],
        'folders': [],
        'pages': [],
    }
    query = assets.Asset.query()
    query = query.filter(assets.Asset.parents == self.key)
    query = query.order(assets.Asset.weight)
    children['assets'] = query.fetch()
    query = pages.Page.query()
    query = query.filter(pages.Page.parents == self.key)
    query = query.order(pages.Page.weight)
    children['pages'] = query.fetch()
    query = Folder.query()
    query = query.filter(Folder.parents == self.key)
    query = query.order(Folder.weight)
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

  @property
  def sync_url(self):
    return '/sync/{}/'.format(self.resource_id)

  @property
  def edit_url(self):
    return EDIT_URL_FORMAT.format(resource_id=self.resource_id)
