from . import models
from google.appengine.ext import ndb
import bs4
import datetime
import html2text


class Page(models.Model):
  resource_id = ndb.StringProperty()
  html = ndb.StringProperty()
  markdown = ndb.StringProperty()
  synced = ndb.DateTimeProperty()
  title = ndb.StringProperty()
  etag = ndb.StringProperty()
  build = ndb.IntegerProperty()
  parents = ndb.KeyProperty(repeated=True)
  unprocessed_html = ndb.StringProperty()
  slug = ndb.StringProperty()

  @classmethod
  def process(cls, resp, unprocessed_content):
    resource_id = resp['id']
    title = resp['title']
    ent = cls.get_or_instantiate(resource_id)
    ent.title = title
    ent.resource_id = resource_id
    ent.unprocessed_html = unprocessed_content
    ent.markdown = cls.convert_html_to_markdown(unprocessed_content)
    ent.html = cls.convert_markdown_to_html(ent.markdown)
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.put()

  @staticmethod
  def convert_html_to_markdown(html):
    soup = bs4.BeautifulSoup(html, 'html.parser')
    content = unicode(soup.body)
    content = content.encode('utf-8')
    return content

  @staticmethod
  def convert_markdown_to_html(content):
    h2t = html2text.HTML2Text()
    content = h2t.handle(content)
    return content
