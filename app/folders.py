import appengine_config
from . import assets
from . import models
from . import pages
from . import messages
from google.appengine.ext import ndb
import datetime
import webapp2

CONFIG = appengine_config.CONFIG
MAIN_FOLDER_ID = CONFIG['folder']
EDIT_URL_FORMAT = "https://drive.google.com/drive/folders/{resource_id}"


class Folder(models.Model):
  updated = ndb.DateTimeProperty(auto_now=True)
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  color = ndb.StringProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.parse_title(resp['title'])
    ent.put()

  @classmethod
  def list(self, parent=None):
    query = Folder.query()
    if parent:
      parent_key = ndb.Key('Folder', parent)
      query = query.filter(Folder.parents == parent_key)
      query = query.order(Folder.weight)
    return query.fetch()

  @property
  def is_asset_folder(self):
    return self.title.lower() == 'assets'

  def list_children(self):
    children = {
        'items': [],
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
    if children['pages']:
      children['items'] += children['pages']
    if children['folders']:
      children['items'] += children['folders']
    if children['items']:
      children['items'] = sorted(children['items'],
                                 key=lambda item: item.weight)
    return children

  @property
  def children(self):
    return self.list_children()

  @webapp2.cached_property
  def parent(self):
    if self.parents:
      return self.parents[0].get()

  @property
  def url(self):
    if self.parent:
      return '/{}/folders/{}/'.format(self.parent.slug, self.key.id())

  @property
  def sync_url(self):
    return '/sync/{}/'.format(self.resource_id)

  @property
  def edit_url(self):
    return EDIT_URL_FORMAT.format(resource_id=self.resource_id)

  @classmethod
  def get_homepage(cls):
    query = cls.query()
    query = query.filter(cls.weight == -1)
    parent_key = ndb.Key(cls.__name__, MAIN_FOLDER_ID)
    query = query.filter(cls.parents == parent_key)
    folder = query.get()
    if folder is None:
      return
    return folder.get_index()

  @classmethod
  def get_resource(cls, resource_id):
    return cls.get(resource_id)

  def get_index(self):
    query = pages.Page.query()
    query = query.filter(pages.Page.weight == -1)
    query = query.filter(pages.Page.parents == self.key)
    return query.get()

  def to_message(self):
    message = messages.FolderMessage()
    message.ident = self.ident
    message.title = self.title
    message.color = self.color
    message.weight = self.weight
    message.edit_url = self.edit_url
    message.synced = self.synced
    message.sync_url = self.sync_url
    message.url = self.url
    return message

  def update(self, message):
    self.color = message.color
    self.put()
