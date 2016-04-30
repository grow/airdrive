from . import admins
from . import approvals
from . import assets
from . import common
from . import downloads
from . import extensions
from . import folders
from . import messages
from . import pages
from . import settings
from . import sync
from datetime import datetime
from google.appengine.api import channel
from google.appengine.api import users
from werkzeug.contrib import cache
import airlock
import appengine_config
import jinja2
import json
import logging
import mimetypes
import os
import time
import webapp2


CONFIG = appengine_config.CONFIG
MAIN_FOLDER_ID = CONFIG['folder']


_here = os.path.dirname(__file__)
_theme_path = os.path.join(_here, '..', 'themes', CONFIG['theme'])
_dist_path = os.path.join(_here, '..', 'dist')
JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_theme_path),
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.loopcontrols',
        extensions.FragmentCacheExtension,
    ],
    autoescape=True)
JINJA.fragment_cache = cache.MemcachedCache()
JINJA.filters['filesizeformat'] = common.do_filesizeformat
JINJA.filters['markdown'] = common.do_markdown


def get_config_content(name):
  path = os.path.join(appengine_config.CONFIG_PATH, 'templates', name)
  return open(path).read()


class Handler(airlock.Handler):

  @property
  def settings(self):
    return settings.Settings.singleton()

  def is_admin(self, redirect=True):
    if not self.me.is_registered:
      if redirect:
        self.redirect(self.urls.sign_in())
      return False
    return admins.Admin.is_admin(self.me.email)
#    try:
#      self.require_admin(admins.Admin.is_admin)
#    except airlock.errors.ForbiddenError:
#      if redirect:
#        self.error(403)
#        html = 'Forbbiden. <a href="{}">Sign out</a>.'.format(self.urls.sign_out())
#        self.response.out.write(html)
#      return False
#    return True

  def render_template(self, path, params=None):
    params = params or {}
    user = users.get_current_user()
    params['config'] = appengine_config
    params['me'] = self.me
    params['urls'] = self.urls
    params['uri_for'] = self.uri_for
    params['statuses'] = messages.Status
    params['get_resource'] = folders.Folder.get_resource
    params['nav'] = folders.get_nav()
    params['get_sibling'] = folders.get_sibling
    params['is_admin'] = self.is_admin(redirect=False)
    template = JINJA.get_template(path)
    html = template.render(params)
    self.response.out.write(html)


class FolderHandler(Handler):

  def get(self, folder_slug, resource_id):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
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
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    page = pages.Page.get(resource_id)
    if page is None:
      self.error(404)
      return
    params = {
        'page': page,
        'pretty_html': page.get_processed_html(),
    }
    self.render_template('page.html', params)


class MainFolderHandler(Handler):

  def get(self, folder_slug):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
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
        'content': get_config_content('welcome.html'),
        'statuses': messages.Status,
    }
    if self.me.registered and not self.me.has_access:
      self.render_template('interstitial_access_request.html', params)
      return
    if self.me.registered and self.me.has_access:
      page = folders.Folder.get_homepage()
      if page is not None:
        self.redirect(page.url)
        return
    self.render_template('interstitial.html', params)


class ThumbnailDownloadHandler(Handler):

  def get(self, resource_id):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    asset = assets.Asset.get(resource_id)
    if asset is None or asset.gcs_thumbnail_path is None:
      self.error(404)
      return
    blob_key = asset.create_blob_key(thumbnail=True)
    self.response.headers['Content-Type'] = 'image/png'
    self.response.headers['X-AppEngine-BlobKey'] = blob_key


class AssetDownloadHandler(Handler):

  def get(self, resource_id):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    asset = assets.Asset.get(resource_id)
    if asset is None or asset.gcs_path is None:
      self.error(404)
      return
    downloads.Download.create(self.me, asset)
    blob_key = asset.create_blob_key()
    self.response.headers['X-AppEngine-BlobKey'] = blob_key
    self.response.headers['Content-Type'] = str(asset.mimetype)
    self.response.headers['Content-Disposition'] = 'attachment; filename={}'.format(asset.title)


class SettingsHandler(Handler):

  def get(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    self.render_template('settings.html')


class AdminApprovalsApprovalHandler(Handler):

  def get(self, ident):
    if not self.is_admin():
      return
    params = {}
    params['approval'] = approvals.Approval.get_by_ident(ident)
    self.render_template('admin_approvals_approval.html', params)


class AdminAdminsHandler(Handler):

  def post(self):
    if not self.is_admin():
      return
    email = self.request.POST['admin.email']
    admins.Admin.create(email, self.me)
    self.get()

  def get(self):
    if not self.is_admin():
      return
    params = {}
    params['admins'] = admins.Admin.list()
    self.render_template('admin_admins.html', params)


class AdminSettingsHandler(Handler):

  def post(self):
    data = dict(self.request.POST)
    for key, value in data.items():
      if not value:
        del data[key]
      if key in settings.Settings.REPEATED_FIELDS:
        if not value:
          data[key] = []
        else:
          data[key] = value.split('\n')
    self.settings.populate(**data)
    self.settings.put()
    self.get()

  def get(self):
    if not self.is_admin():
      return
    params = {}
    params['approvals'] = approvals.Approval.search()
    params['admins'] = admins.Admin.list()
    params['folder'] = folders.Folder.get(MAIN_FOLDER_ID)
    params['assets'] = assets.Asset.search_by_downloads()
    params['settings'] = self.settings
    self.render_template('admin_settings.html', params)


class AdminHandler(Handler):

  def get(self, template='builds'):
    if not self.is_admin():
      return
    if self.request.GET.get('format') == 'csv':
      content = approvals.Approval.to_csv()
      self.response.headers['Content-Type'] = 'text/csv'
      self.response.out.write(content)
      return
    params = {}
    params['approvals'] = approvals.Approval.search()
    params['admins'] = admins.Admin.list()
    params['folder'] = folders.Folder.get(MAIN_FOLDER_ID)
    params['assets'] = assets.Asset.search_by_downloads()
    try:
      self.render_template('admin_{}.html'.format(template), params)
    except jinja2.TemplateNotFound:
      self.error(404)
      return


class SyncHandler(Handler):

  def get(self, resource_id=MAIN_FOLDER_ID):
    if not self.is_admin():
      return
    try:
      sync.download_resource(resource_id, self.me)
    except Exception as e:
      logging.exception('Sync error.')
      self.response.status = 500
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(str(e))
      return
    token = channel.create_channel(self.me.ident)
    content = json.dumps({
        'token': token,
    })
    self.response.out.write(content)


class DeleteHandler(Handler):

  def get(self, resource_id):
    if not self.is_admin():
      return
    page = pages.Page.get(resource_id)
    if page:
      page.delete()
      self.response.out.write('deleted')
    else:
      folder = folders.Folder.get(resource_id)
      if folder:
        folder.delete()
        self.response.out.write('deleted')
