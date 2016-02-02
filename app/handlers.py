from . import admins
from . import approvals
from . import assets
from . import common
from . import downloads
from . import folders
from . import messages
from . import pages
from . import settings
from . import sync
from google.appengine.api import channel
from google.appengine.api import users
import airlock
import appengine_config
import jinja2
import json
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
JINJA.filters['markdown'] = common.do_markdown


def get_config_content(name):
  path = os.path.join(appengine_config.CONFIG_PATH, 'templates', name)
  return open(path).read()


class Handler(airlock.Handler):

  @property
  def settings(self):
    return settings.Settings.singleton()

  def require_admin(self):
    if appengine_config.OFFLINE:
      return
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    if not self.is_admin():
      return

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
    params['statuses'] = messages.Status

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
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    page = pages.Page.get(resource_id)
    if page is None:
      self.error(404)
      return
    params = {
        'page': page,
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

  def post(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in(webapp2.uri_for('home')))
      return
    form_dict = dict(self.request.POST)
    if 'email_opt_in' in form_dict:
      form_dict['email_opt_in'] = True
    approval_form_message = approvals.Approval.decode_form(form_dict)
    approvals.Approval.create(approval_form_message, self.me)
    self.get()

  def get(self):
    params = {
        'content': get_config_content('welcome.html'),
        'statuses': messages.Status,
    }
    if self.me.registered and not self.me.has_access:
      self.render_template('interstitial_access_request.html', params)
      return
    self.render_template('interstitial.html', params)


class AssetDownloadHandler(Handler):

  def get(self, resource_id):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    asset = assets.Asset.get(resource_id)
    if asset is None:
      self.error(404)
      return
    downloads.Download.create(self.me, asset)
    self.response.status = 302
    self.response.headers['Location'] = str(asset.url)


class SettingsHandler(Handler):

  def get(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    self.render_template('settings.html')


class AdminApprovalsApprovalHandler(Handler):

  def get(self, ident):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    if not self.is_admin():
      return
    params = {}
    params['approval'] = approvals.Approval.get_by_ident(ident)
    self.render_template('admin_approvals_approval.html', params)


class AdminAdminsHandler(Handler):

  def post(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
    if not self.is_admin():
      return
    email = self.request.POST['admin.email']
    admins.Admin.create(email, self.me)
    self.get()

  def get(self):
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
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
    if not self.me.is_registered:
      self.redirect(self.urls.sign_in())
      return
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
    self.require_admin()
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
    sync.download_resource(resource_id, self.me)
    token = channel.create_channel(self.me.ident)
    content = json.dumps({
        'token': token,
    })
    self.response.out.write(content)


class DeleteHandler(Handler):

  def get(self, resource_id):
    page = pages.Page.get(resource_id)
    if page:
      page.delete()
      self.response.out.write('deleted')
    else:
      folder = folders.Folder.get(resource_id)
      if folder:
        folder.delete()
        self.response.out.write('deleted')
