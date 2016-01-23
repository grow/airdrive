from . import common
from . import folders
from . import pages
from . import sync
from google.appengine.api import users
import appengine_config
import jinja2
import os
import webapp2


CONFIG = appengine_config.CONFIG


_here = os.path.dirname(__file__)
_theme_path = os.path.join(_here, '..', 'themes', CONFIG['theme'])
JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_theme_path),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
JINJA.filters['filesizeformat'] = common.do_filesizeformat


class Handler(webapp2.RequestHandler):

  def render_template(self, path, params):
    user = users.get_current_user()
    params['config'] = appengine_config
    params['user'] = user
    template = JINJA.get_template(path)
    html = template.render(params)
    self.response.out.write(html)


class FolderHandler(Handler):

  def get(self, folder_slug, subfolder_short_id):
    folder_ents = folders.Folder.list(
        parent=CONFIG['folder'],
    )
    folder = folders.Folder.get(subfolder_short_id)
    if folder is None:
      self.error(404)
      return
    params = {
        'folder': folder,
        'folders': folder_ents,
    }
    self.render_template('folder.html', params)


class PageHandler(Handler):

  def get(self, folder_slug, page_short_id, page_slug):
    folder_ents = folders.Folder.list(
        parent=CONFIG['folder'],
    )
    page = pages.Page.get(page_short_id)
    if page is None:
      self.error(404)
      return
    params = {
        'folders': folder_ents,
        'page': page,
    }
    self.render_template('page.html', params)


class SyncHandler(Handler):

  def get(self):
    resource_id = CONFIG['folder']
    resp = sync.download_resource(resource_id)
    folder = folders.Folder.get(resource_id)
    children = folder.list_children()
    self.response.out.write(children)
