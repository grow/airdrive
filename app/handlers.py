from . import admins
from . import approvals
from . import assets
from . import common
from . import downloads
from . import extensions
from . import folders
from . import index
from . import messages
from . import pages
from . import settings
from . import sync
from . import users as app_users
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
SETTINGS = settings.Settings.singleton()

_here = os.path.dirname(__file__)
_default_theme_path = os.path.join(_here, '..', 'themes', appengine_config.DEFAULT_THEME)
_theme_path = os.path.join(_here, '..', 'themes', SETTINGS.get_theme())
_dist_path = os.path.join(_here, '..', 'dist')
JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader([
        _theme_path,
        _default_theme_path,
    ]),
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.do',
        'jinja2.ext.loopcontrols',
        'jinja2.ext.with_',
        extensions.FragmentCacheExtension,
],
    autoescape=True)
JINJA.fragment_cache = cache.MemcachedCache()
JINJA.filters['filesizeformat'] = common.do_filesizeformat
JINJA.filters['markdown'] = common.do_markdown
JINJA.filters['stripext'] = common.do_stripext


def get_config_content(name):
    path = os.path.join(appengine_config.CONFIG_PATH, 'templates', name)
    return open(path).read()


class Handler(airlock.Handler):

#  @webapp2.cached_property
#  def me(self):
#    return app_users.User.get_by_email('user@example.com')

    @property
    def settings(self):
        return settings.Settings.singleton()

    def is_admin(self, redirect=True):
        if not self.me.is_registered:
            if redirect:
                self.redirect(self.urls.sign_in())
            return False
        return admins.Admin.is_admin(self.me.email)

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
        params['settings'] = self.settings
        params['get_sibling'] = folders.get_sibling
        params['get_page'] = pages.Page.get
        params['has_access'] = self.me.has_access_to_folder
        params['can_access_resource'] = self.me.can_access_resource
        params['is_admin'] = self.is_admin(redirect=False)
        params['top_folders'] = \
            folders.Folder.list_top(include_draft=params['is_admin'])
        template = JINJA.get_template(path)
        html = template.render(params)
        self.response.out.write(html)


class FolderHandler(Handler):

    def get(self, folder_slug, resource_id):
        if not self.me.is_registered:
            self.redirect(self.urls.sign_in())
            return
        if not self.me.has_access:
            self.redirect('/')
            return
        folder = folders.Folder.get(resource_id)
        if folder is None:
            self.error(404)
            return
        params = {
            'folder': folder,
            'is_admin': self.is_admin(redirect=False),
        }
        self.render_template('folder.html', params)


class SearchHandler(Handler):

    def get(self):
        if not self.me.is_registered:
            self.redirect(self.urls.sign_in())
            return
        query = self.request.GET.get('q')
        params = {}
        if query:
            params['query'] = query
            result = index.do_search(query)
            params['result'] = result
        root_folder_id = sync.get_root_folder_id()
        params['folder'] = folders.Folder.get(root_folder_id)
        self.render_template('search.html', params)


class PageHandler(Handler):

    def get(self, folder_slug, resource_id, page_slug):
        if not self.me.is_registered:
            self.redirect(self.urls.sign_in())
            return
        if not self.me.has_access:
            self.redirect('/')
            return
        page = pages.Page.get(resource_id)
        if page is None:
            self.error(404)
            return
        html = page.get_processed_html()
        content_template = None
        try:
            content_template = JINJA.from_string(html)
        except:
            if isinstance(html, unicode):
                html = html.encode('utf-8')
            logging.exception('Error parsing template.')
            logging.error(html)
            try:
                sync.download_resource(resource_id, self.me, queue='default')
                page = pages.Page.get(resource_id)
                html = page.get_processed_html()
                content_template = JINJA.from_string(html)
            except:
                logging.exception('Tried syncing but failed.')
                pass
        if not content_template:
            self.error(500)
            return
        rendered_html = content_template.render({
            'asset': lambda *args, **kwargs: None,
            'get_asset': assets.Asset.get,
            'get_page': pages.Page.get,
            'get_folder': folders.Folder.get,
            'is_admin': self.is_admin(redirect=False),
        })
        params = {
            'page': page,
            'is_admin': self.is_admin(redirect=False),
            'pretty_html': rendered_html,
        }
        template = page.template or (page.parent and page.parent.template) or 'page.html'
        self.render_template(template, params)


class MainFolderHandler(Handler):

    def get(self, folder_slug):
        root_folder_id = sync.get_root_folder_id()
        if not self.me.is_registered:
            self.redirect(self.urls.sign_in())
            return
        if not self.me.has_access:
            self.redirect('/')
            return
        folder = folders.Folder.get_by_slug(folder_slug, parent=root_folder_id)
        if folder is None:
            self.error(404)
            return
        params = {
            'folder': folder,
            'settings': self.settings,
        }
        self.render_template('folder.html', params)


class HomepageHandler(Handler):

    def post(self):
        if not self.me.is_registered:
            self.redirect(self.urls.sign_in(webapp2.uri_for('home')))
            return
        form_dict = dict(self.request.POST)
        folders = self.request.POST.getall('folder')
        if 'email_opt_in' in form_dict:
            form_dict['email_opt_in'] = True
        form = approvals.Approval.decode_form(form_dict)
        form.folders = folders
        approvals.Approval.get_or_create(
            form, self.me, status=messages.Status.PENDING)
        self.get()


    def get(self):
        params = {
            'content': get_config_content('welcome.html'),
            'statuses': messages.Status,
            'settings': self.settings,
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
        params = {}
        params['admin_page'] = True
        self.render_template('settings.html', params)


class AdminApprovalsApprovalHandler(Handler):

    def get(self, ident):
        if not self.is_admin():
            return
        params = {}
        params['approval'] = approvals.Approval.get_by_ident(ident)
        params['admin_page'] = True
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
        params['admin_page'] = True
        self.render_template('admin_admins.html', params)


class AdminSettingsHandler(Handler):

    def get(self):
        if not self.is_admin():
            return
        root_folder_id = sync.get_root_folder_id()
        params = {}
        params['admin_page'] = True
        params['approvals'] = approvals.Approval.search()
        params['admins'] = admins.Admin.list()
        params['folder'] = folders.Folder.get(root_folder_id)
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
        root_folder_id = sync.get_root_folder_id()
        params = {}
        params['admin_page'] = True
        params['approvals'] = approvals.Approval.search()
        params['admins'] = admins.Admin.list()
        params['folder'] = folders.Folder.get(root_folder_id)
        params['assets'] = assets.Asset.search_by_downloads()
        try:
            self.render_template('admin_{}.html'.format(template), params)
        except jinja2.TemplateNotFound:
            self.error(404)
            return


class SyncHandler(Handler):

    def get(self, resource_id=None):
        if resource_id is None:
            root_folder_id = sync.get_root_folder_id()
            resource_id = root_folder_id
        if not self.is_admin():
            return
        try:
            sync.download_resource(resource_id, self.me, queue='default')
        except Exception as e:
            logging.exception('Sync error.')
            self.response.status = 500
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(str(e))
            return
        try:
            token = channel.create_channel(self.me.ident)
            content = json.dumps({
                'token': token,
            })
            self.response.out.write(content)
        except channel.AppIdAliasRequired:
            logging.warn('AppIdAliasRequired raised.')
            self.response.out.write('Started sync: {}'.format(resource_id))


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


class ImportCsvHandler(Handler):

    def post(self):
        if not self.is_admin():
            return
        content = self.request.get('file')
        app_users.User.import_from_csv(content, updated_by=self.me)
