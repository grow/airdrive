import appengine_config
from . import assets
from . import models
from . import pages
from . import messages
from google.appengine.api import memcache
from google.appengine.ext import ndb
import datetime
import re
import pickle
import webapp2

CONFIG = appengine_config.CONFIG
MAIN_FOLDER_ID = CONFIG['folder']
EDIT_URL_FORMAT = "https://drive.google.com/drive/folders/{resource_id}"
NAV_CACHE_KEY = 'nav-2345'


class Cache(ndb.Model):
  content = ndb.TextProperty()


def get_nav():
#  nav_cache = Cache(id='nav').key.get()
#  if nav_cache and nav_cache.content:
#    return pickle.loads(nav_cache.content)
  nav = memcache.get(NAV_CACHE_KEY)
  if nav is None:
    nav = create_nav()
  return nav


def create_nav():
  nav = []
  root_folders = Folder.list(parent=MAIN_FOLDER_ID, use_cache=True)
  for root_folder in root_folders:
    nav.append(update_nav(root_folder))
  memcache.set(NAV_CACHE_KEY, nav)
#  nav_cache = Cache(id='nav')
#  nav_cache.content = pickle.dumps(nav)
#  nav_cache.put()
  return nav


def update_nav_item(page):
  item = {}
  item['resource_type'] = page.resource_type
  item['resource_id'] = page.resource_id
  item['url'] = page.url
  item['is_asset_folder'] = (
      page.resource_type == 'Folder'
      and page.is_asset_folder)
  item['title'] = page.title
  item['weight'] = page.weight
  return item


def update_nav_pages(pages):
  return [update_nav_item(item) for item in pages
          if not item.draft]


def update_nav(folder):
  root = {}
  if folder.draft or folder.internal:
    root['folder'] = {}
    return root['folder']
  children = folder.list_children()
  root['weight'] = folder.weight
  root['folder'] = update_nav_item(folder)
  root['folder']['children'] = {}
  root['folder']['children']['folders'] = [
      update_nav(sub_folder)
      for sub_folder in children['folders']
      if not sub_folder.draft]
  root['folder']['children']['pages'] = [
      update_nav_item(page)
      for page in children['pages']
      if not page.draft]
  root['folder']['children']['items'] = (
      root['folder']['children']['folders']
      + root['folder']['children']['pages'])
  return root


def get_sibling(page, next=True):
  nav = get_nav()
  for n, folder in enumerate(nav):
    if 'folder' not in folder:
        continue
    page_items = folder['folder']['children']['items']
    for i, page_item in enumerate(page_items):
      if page.resource_id == page_item.get('resource_id'):
        if next:
          if i + 1 == len(page_items):
            if n + 1 == len(nav):
              return None
            if 'folder' in nav[n + 1]:
              sibling = nav[n + 1]['folder']['children']
              if sibling['items']:
                return sibling['items'][0]
            return None
          return page_items[i + 1]
        if i - 1 < 0:
          if n - 1 < 0:
            return None
          if 'folder' in nav[n - 1]:
            sibling = nav[n - 1]['folder']['children']
            if sibling['items']:
              return sibling['items'][-1]
          return None
        return page_items[i - 1]


class Folder(models.BaseResourceModel):
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
  def list(self, parent=None, use_cache=True):
    cache_key = 'Folder:List:{}'.format(MAIN_FOLDER_ID)
    if use_cache and parent is None:
      ents = memcache.get(cache_key)
      if ents:
        return ents
    query = Folder.query()
    if parent:
      parent_key = ndb.Key('Folder', parent)
      query = query.filter(Folder.parents == parent_key)
      query = query.order(Folder.weight)
    ents = query.fetch()
    memcache.set(cache_key, ents)
    return ents

  @classmethod
  def clear_cache(cls):
    cache_key = 'Folder:List:{}'.format(MAIN_FOLDER_ID)
    memcache.delete(cache_key)

  @property
  def is_asset_folder(self):
    return bool(re.match('^assets', self.title.lower()))

  @property
  def is_overview_folder(self):
    return self.title.lower() in ['overview', 'welcome'] and self.weight == -1

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

  @webapp2.cached_property
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
    message.resource_id = self.resource_id
    message.draft = self.draft
    return message

  def update(self, message):
    self.color = message.color
    self.put()
