import appengine_config
from . import models
from . import process
from google.appengine.ext import ndb
from google.appengine.api import memcache
from markdown.extensions import tables
from markdown.extensions import toc
import datetime
import html2text
import logging
import markdown
import re
import webapp2

EDIT_URL_FORMAT = 'https://docs.google.com/document/d/{resource_id}/edit'


class Page(models.BaseResourceModel):
  html = ndb.TextProperty()
  markdown = ndb.TextProperty()
  etag = ndb.StringProperty()
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  unprocessed_html = ndb.TextProperty()
  processed_html = ndb.TextProperty()
  locale = ndb.StringProperty()

  def __repr__(self):
    return '[Page: {} ({})]'.format(self.title, self.resource_id)

  def __eq__(self, other):
    return (
        isinstance(other, Page)
        and self.key.id() == other.key.id())

  @property
  def _html_cache_key(self):
    return 'page:{}:{}'.format(self.resource_id, appengine_config.VERSION)

  def _pre_put_hook(self):
    memcache.delete(self._html_cache_key)

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    etag = resp['etag']
    ent = cls.get_or_instantiate(resource_id)
    ent.parse_title(resp['title'])
    ent.resource_id = resource_id
    ent.etag = etag
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.put()
    return ent

  def process_content(self, unprocessed_content):
    self.unprocessed_html = unprocessed_content
    self.processed_html = process.process_html(unprocessed_content)
    self.put()

  def should_process_content(self, resp):
    return True
    return self.etag != resp['etag']

  @webapp2.cached_property
  def parent(self):
    return self.parents[0].get()

  @property
  def url(self):
    return '/{}/{}/{}/'.format(self.parent.slug, self.key.id(), self.slug)

  @property
  def edit_url(self):
    return EDIT_URL_FORMAT.format(resource_id=self.resource_id)

  @property
  def sync_url(self):
    return '/sync/{}/'.format(self.resource_id)

  def get_processed_html(self):
    if self.processed_html:
      return self.processed_html
    return self.pretty_html

  @property
  def pretty_html(self):
    html = memcache.get(self._html_cache_key)
    if html is not None:
      return html
    html = process.process_html(self.unprocessed_html)
    memcache.set(self._html_cache_key, html)
    return html

def render_folder(tag_name, resource_id, *args, **kwargs):
  return '{{render_mosaic({})}}'.format(resource_id)
