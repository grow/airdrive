import appengine_config
from . import assets
from . import models
from . import pages
from . import messages
from . import settings
from google.appengine.api import memcache
from google.appengine.ext import ndb
import datetime
import logging
import re
import pickle
import webapp2

CONFIG = appengine_config.CONFIG
EDIT_URL_FORMAT = "https://drive.google.com/drive/folders/{resource_id}"
NAV_CACHE_KEY = 'nav'


class Cache(ndb.Model):
  content = ndb.TextProperty()


def get_nav(include_draft=True):
  nav = memcache.get(NAV_CACHE_KEY + str(include_draft))
  if nav is None:
    nav = create_nav(include_draft=include_draft)
  return nav


def create_nav(include_draft=True):
  from . import sync
  root_folder_id = sync.get_root_folder_id()
  nav = []
  root_folders = Folder.list(
      parent=root_folder_id, use_cache=True,
      include_draft=include_draft)
  for root_folder in root_folders:
    item = update_nav(root_folder, include_draft=include_draft)
    if item:
      nav.append(item)
  memcache.set(NAV_CACHE_KEY + str(include_draft), nav)
  return nav


def update_nav_item(page):
  item = {}
  item['color'] = page.color
  item['resource_type'] = page.resource_type
  item['resource_id'] = page.resource_id
  item['url'] = page.url
  item['hidden'] = page.hidden
  item['draft'] = page.draft
  item['is_index'] = page.is_index
  item['is_asset_container'] = (
      page.resource_type == 'Folder'
      and page.is_asset_container)
  item['is_asset_folder'] = (
      page.resource_type == 'Folder'
      and page.is_asset_folder)
  item['top'] = page.top
  item['title'] = page.title
  item['is_public'] = page.is_public
  item['is_parent'] = page.is_parent
  item['weight'] = page.weight
  return item


def update_nav(folder, include_draft=True):
  if folder.hidden or folder.internal or folder.draft and not include_draft:
    return {}
  root = {}
  root['weight'] = folder.weight
  root['folder'] = update_nav_item(folder)
  root['folder']['children'] = {}
  children = folder.list_children(include_draft=include_draft)
  root['folder']['children']['folders'] = [
      update_nav(sub_folder, include_draft=include_draft)
      for sub_folder in children['folders']
      if not sub_folder.hidden]
  root['folder']['children']['pages'] = [
      update_nav_item(page)
      for page in children['pages']
      if not page.hidden]
  items = (
      root['folder']['children']['folders']
      + root['folder']['children']['pages'])
  items.sort(key=lambda item: item['weight'])
  root['folder']['children']['items'] = items
  return root



def get_sibling(page, next=True, is_admin=False, nav=None):
  nav = get_nav(include_draft=bool(is_admin)) if nav is None else nav
  for n, folder in enumerate(nav):
    if 'folder' not in folder:
        continue
    page_items = folder['folder']['children']['items']
    for i, page_item in enumerate(page_items):
      if isinstance(page, dict):
        resource_id = page['resource_id']
      else:
        resource_id = page.resource_id
      if resource_id != page_item.get('resource_id'):
        continue
      if next:
        if i + 1 == len(page_items):
          if n + 1 == len(nav):
            return None
          if 'folder' in nav[n + 1]:
            sibling = nav[n + 1]['folder']['children']
            if sibling['items']:
              result = sibling['items'][0]
              return process_result(result, next=next)
          return None
        result = page_items[i + 1]
        return process_result(result, next=next)
      if i - 1 < 0:
        if n - 1 < 0:
          return None
        if 'folder' in nav[n - 1]:
          sibling = nav[n - 1]['folder']['children']
          if sibling['items']:
            result = sibling['items'][-1]
            return process_result(result, next=next)
        return None
      result = page_items[i - 1]
      return process_result(result, next=next)


def process_result(resource, next=True):
  if 'folder' in resource and resource['folder']:
      sub_resource = resource['folder']
      if 'children' in sub_resource and not sub_resource['is_asset_folder'] and not sub_resource['is_asset_container']:
          if sub_resource['children']['items']:
              if next:
                  return process_result(sub_resource['children']['items'][0], next=next)
              return sub_resource['children']['items'][-1]
  return resource


class Folder(models.BaseResourceModel):
  updated = ndb.DateTimeProperty(auto_now=True)
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  color = ndb.StringProperty()
  container = ndb.BooleanProperty()

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
  def list(self, parent=None, use_cache=True, include_draft=False):
    from . import sync
    root_folder_id = sync.get_root_folder_id()
    cache_key = 'Folder:List:{}:{}'.format(root_folder_id, str(include_draft))
    if use_cache and parent is None:
      ents = memcache.get(cache_key)
      if ents:
        return ents
    query = Folder.query()
    if parent:
      parent_key = ndb.Key('Folder', parent)
      query = query.filter(Folder.parents == parent_key)
      if not include_draft:
          query = query.filter(Folder.draft == False)
      query = query.order(Folder.weight)
    ents = query.fetch()
    memcache.set(cache_key, ents)
    return ents

  @classmethod
  def clear_cache(cls):
    from . import sync
    root_folder_id = sync.get_root_folder_id()
    cache_key = 'Folder:List:{}'.format(root_folder_id)
    memcache.delete(cache_key)

  @property
  def is_asset_folder(self):
    return (self.is_asset_container
            or (bool(re.match('^assets', self.title.lower())) and not self.is_parent))

  @property
  def is_overview_folder(self):
    return self.title.lower() in ['overview', 'welcome'] and self.weight == -1

  @classmethod
  def list_top(cls, include_draft=False):
    top_items = []
    nav = get_nav(include_draft=include_draft)

    def process_sub_items(sub_items):
      for item in sub_items:
        if 'folder' in item and item['folder'].get('top'):
          top_items.append(item)

    for item in nav[1:]:
      if 'folder' in item:
        top_items.append(item)
        process_sub_items(item['folder']['children']['folders'])

    return top_items

  def list_children(self, include_draft=True):
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

    if not include_draft:
        children['pages'] = [page for page in children['pages'] if not page.draft]
        children['assets'] = [folder for folder in children['assets'] if not folder.draft]
        children['folders'] = [folder for folder in children['folders'] if not folder.draft]
        children['items'] = [item for item in children['items'] if not item.draft]

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
    from . import sync
    root_folder_id = sync.get_root_folder_id()
    query = cls.query()
    query = query.filter(cls.weight == -1)
    parent_key = ndb.Key(cls.__name__, root_folder_id)
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
    message.hidden = self.hidden
    children = self.list_children()
    if children['pages']:
        message.pages = []
        for child in children['pages']:
            message.pages.append(child.to_message())
    return message

  def update(self, message):
    self.color = message.color
    self.put()

  @classmethod
  def get_sync_tree(cls):
    from . import sync
    root_folder_id = sync.get_root_folder_id()
    service = sync.get_service()
    page_token = None
    childs = []
    while True:
      params = {}
      if page_token:
        params['pageToken'] = page_token
      children = service.children().list(
          folderId=root_folder_id, **params).execute()
      for child in children.get('items', []):
        childs.append(child)
      page_token = children.get('nextPageToken')
      if not page_token:
        break
    return childs
