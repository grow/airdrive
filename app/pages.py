from . import models
from google.appengine.ext import ndb
from markdown.extensions import tables
from markdown.extensions import toc
import bleach
import bbcode
import bs4
import datetime
import html2text
import logging
import markdown
import re
import webapp2

EDIT_URL_FORMAT = 'https://docs.google.com/document/d/{resource_id}/edit'


class Page(models.Model):
  html = ndb.TextProperty()
  markdown = ndb.TextProperty()
  etag = ndb.StringProperty()
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  unprocessed_html = ndb.TextProperty()
  locale = ndb.StringProperty()

  @classmethod
  def process(cls, resp):
    resource_id = resp['id']
    etag = resp['etag']
    ent = cls.get_or_instantiate(resource_id)
    ent.title, ent.weight = cls.parse_title_and_weight(resp['title'])
    ent.resource_id = resource_id
    ent.etag = etag
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.put()
    return ent

  def process_content(self, unprocessed_content):
    self.unprocessed_html = unprocessed_content
    self.markdown = self.convert_html_to_markdown(unprocessed_content)
    self.html = self.convert_markdown_to_html(self.markdown)
    self.put()

  def should_process_content(self, resp):
    return True
    return self.etag != resp['etag']

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
    return '/sync/{}/'.format(self.resource_id)

  @property
  def pretty_html(self):
    ATTRS = ['src', 'href', 'style']
    TAGS = [
        'p', 'b', 'i', 'em', 'br', 'table', 'tr', 'td', 'tbody',
        'h2', 'h1', 'a', 'h3', 'ul', 'li', 'ol', 'img', 'u', 'hr',
        'sup', 'strong',
    ]
    html = self.unprocessed_html
    soup = bs4.BeautifulSoup(html)
    html = soup.body.prettify()
    html = bleach.clean(html,
        tags=TAGS,
        attributes=ATTRS,
        strip=True)
    html = self.markdownify(html)
#    html = self.bbcodeify(html)
    return html

  @classmethod
  def markdownify(cls, html):
    html = re.sub('\_{2}(.+)\_{2}', '<i>\\1</i>', html, re.MULTILINE)
    html = re.sub('\*{2}(.+)\*{2}', '<strong>\\1</strong>', html, re.MULTILINE)
    html = re.sub('\[COLOR:([^\]]*)\]', '<div class="page-component-color" style="background-color:\\1"></div>', html, re.MULTILINE)
    html = html.replace('[TOC]', '<div class="toc toc--auto"><ul></ul></div>')
    html = re.sub('\[BUTTON:([^\]]*)\]([^\]]*)\[/\]', '<a class="btn" href="\\1">\\2</a>', html, re.MULTILINE)
    return html

  @classmethod
  def bbcodeify(cls, html):
    parser = bbcode.Parser(
        escape_html=False,
        normalize_newlines=False,
        newline='')
#    parser.add_formatter('FOLDER', render_folder)
    return parser.format(html)


def render_folder(tag_name, resource_id, *args, **kwargs):
  return '{{render_mosaic({})}}'.format(resource_id)
