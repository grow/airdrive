from . import models
from google.appengine.ext import ndb
from markdown.extensions import tables
from markdown.extensions import toc
import bleach
import bs4
import datetime
import html2text
import logging
import markdown
import re
import webapp2

EDIT_URL_FORMAT = 'https://docs.google.com/document/d/{resource_id}/edit'


class Page(models.Model):
  resource_id = ndb.StringProperty()
  html = ndb.TextProperty()
  markdown = ndb.TextProperty()
  synced = ndb.DateTimeProperty()
  title = ndb.StringProperty()
  etag = ndb.StringProperty()
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  unprocessed_html = ndb.TextProperty()
  slug = ndb.ComputedProperty(lambda self: self.generate_slug(self.title))
  modified = ndb.DateTimeProperty()

  @classmethod
  def process(cls, resp, unprocessed_content):
    resource_id = resp['id']
    title = resp['title']
    etag = resp['etag']
    ent = cls.get_or_instantiate(resource_id)
    ent.title = title
    ent.resource_id = resource_id
    ent.etag = etag
    ent.unprocessed_html = unprocessed_content
    ent.markdown = cls.convert_html_to_markdown(unprocessed_content)
    ent.html = cls.convert_markdown_to_html(ent.markdown)
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.put()

  @classmethod
  def should_reprocess(cls, resp):
    resource_id = resp['id']
    ent = cls.get(resource_id)
    if ent is None:
      return True
    return ent.etag != resp['etag']

  @staticmethod
  def convert_html_to_markdown(html):
    h2t = html2text.HTML2Text()
    h2t.bypass_tables = True
    h2t.ignore_images = True
    content = h2t.handle(html)
    return content

  @staticmethod
  def convert_markdown_to_html(content):
    extensions = [
        tables.TableExtension(),
        toc.TocExtension(),
    ]
    return markdown.markdown(content, extensions=extensions)

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
    return '/sync/{}'.format(self.resource_id)

  @property
  def pretty_html(self):
    ATTRS = ['src', 'href', 'style']
    TAGS = [
        'p', 'b', 'i', 'em', 'br', 'table', 'tr', 'td', 'tbody',
        'h2', 'h1', 'a', 'h3', 'ul', 'li', 'ol', 'img', 'u', 'hr',
    ]
    html = self.unprocessed_html
    soup = bs4.BeautifulSoup(html)
    html = soup.body.prettify()
    html = bleach.clean(html,
        tags=TAGS,
        attributes=ATTRS,
        strip=True)
    html = self.markdownify(html)
    return html

  @classmethod
  def markdownify(cls, html):
    html = re.sub('\_{2}(.+)\_{2}', '<i>\\1</i>', html, re.MULTILINE)
    html = re.sub('\*{2}(.+)\*{2}', '<strong>\\1</strong>', html, re.MULTILINE)
    html = re.sub('\[COLOR:([^\]]*)\]', '<div class="page-component-color" style="background-color:\\1"></div>', html, re.MULTILINE)
    html = html.replace('[TOC]', '<div class="toc toc--auto"><ul></ul></div>')
    return html
