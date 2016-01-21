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

  @classmethod
  def process(cls, resp, unprocessed_content):
    resource_id = resp['id']
    title = resp['title']
    page = cls.get_or_instantiate(resource_id)
    page.title = title
    page.markdown = cls.convert_html_to_markdown(unprocessed_content)
    page.html = cls.convert_markdown_to_html(page.markdown)
    page.synced = datetime.datetime.now()
    page.put()

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
