import airlock
from . import admins
from . import assets
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
MAIN_FOLDER_ID = CONFIG['folder']


_here = os.path.dirname(__file__)
_theme_path = os.path.join(_here, '..', 'themes', CONFIG['theme'])
JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_theme_path),
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.loopcontrols',
    ],
    autoescape=True)
JINJA.filters['filesizeformat'] = common.do_filesizeformat


def get_config_content(name):
  path = os.path.join(appengine_config.CONFIG_PATH, 'templates', name)
  return open(path).read()


class Handler(airlock.Handler):

  def is_admin(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    try:
      self.require_admin(admins.Admin.is_admin)
    except airlock.errors.ForbiddenError:
      self.error(403)
      html = 'Forbbiden. <a href="{}">Sign out</a>.'.format(self.urls.sign_out())
      self.response.out.write(html)
      return
    return True

  def render_template(self, path, params=None):
    params = params or {}
    user = users.get_current_user()
    params['config'] = appengine_config
    params['me'] = self.me
    params['urls'] = self.urls
    params['uri_for'] = self.uri_for

    folder_ents = folders.Folder.list(parent=MAIN_FOLDER_ID)
    params['folders'] = folder_ents

    template = JINJA.get_template(path)
    html = template.render(params)
    self.response.out.write(html)


class FolderHandler(Handler):

  def get(self, folder_slug, resource_id):
    folder = folders.Folder.get(resource_id)
    if folder is None:
      self.error(404)
      return
    params = {
        'folder': folder,
    }
    self.render_template('folder.html', params)


class PageHandler(Handler):

  def get(self, folder_slug, resource_id, page_slug):
    page = pages.Page.get(resource_id)
    if page is None:
      self.error(404)
      return
    params = {
        'page': page,
    }
    self.render_template('page.html', params)


class SyncHandler(Handler):

  def get(self, resource_id=MAIN_FOLDER_ID):
    resp = sync.download_resource(resource_id)
    self.response.out.write('done')


class MainFolderHandler(Handler):

  def get(self, folder_slug):
    folder = folders.Folder.get_by_slug(folder_slug, parent=MAIN_FOLDER_ID)
    if folder is None:
      self.error(404)
      return
    params = {
        'folder': folder,
    }
    self.render_template('folder.html', params)


class HomepageHandler(Handler):

  def get(self):
    params = {
        'content': get_config_content('welcome.html')
    }
    if self.me.registered and not self.me.has_access:
      self.render_template('interstitial_access_request.html', params)
      return
    self.render_template('interstitial.html', params)


class AssetDownloadHandler(Handler):

  def get(self, resource_id):
    asset = assets.Asset.get(resource_id)
    if asset is None:
      self.error(404)
      return
    self.response.status = 302
    self.response.headers['Location'] = str(asset.url)


class SettingsHandler(Handler):

  def get(self):
    self.render_template('settings.html')


class AdminHandler(Handler):

  def get(self, template='builds'):
    if not self.is_admin():
      return
    try:
      self.render_template('admin_{}.html'.format(template))
    except jinja2.TemplateNotFound:
      self.error(404)
      return
