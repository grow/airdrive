from . import handlers
from . import services
from protorpc.wsgi import service
import airlock
import os
import appengine_config
import webapp2

airlock.set_config(appengine_config.AIRLOCK_CONFIG)
CONFIG = appengine_config.CONFIG


routes = [
    webapp2.Route('/sync/<resource_id>', handlers.SyncHandler),
    webapp2.Route('/sync/', handlers.SyncHandler, name='sync'),
    webapp2.Route('/delete/<resource_id>/', handlers.DeleteHandler, name='delete'),
    webapp2.Route('/thumbnails/<resource_id>', handlers.ThumbnailDownloadHandler, name='thumbnail'),
    webapp2.Route('/assets/<resource_id>', handlers.AssetDownloadHandler, name='asset'),
    webapp2.Route('/settings/', handlers.SettingsHandler, name='settings'),
    webapp2.Route('/admin/importcsv', handlers.ImportCsvHandler, name='admin-import-csv'),
    webapp2.Route('/admin/approvals/<ident>/', handlers.AdminApprovalsApprovalHandler, name='admin-approvals-approval'),
    webapp2.Route('/admin/settings/', handlers.AdminSettingsHandler, name='admin-settings'),
    webapp2.Route('/admin/admins/', handlers.AdminAdminsHandler, name='admin-admins'),
    webapp2.Route('/admin/<template>/', handlers.AdminHandler, name='admin-page'),
    webapp2.Route('/admin/', handlers.AdminHandler, name='admin'),
    webapp2.Route('/<folder_slug>/folders/<resource_id>/', handlers.FolderHandler),
    webapp2.Route('/<folder_slug>/<resource_id>/<page_slug>/', handlers.PageHandler),
    webapp2.Route('/<folder_slug>/', handlers.MainFolderHandler, name='main-folder'),
    webapp2.Route('/', handlers.HomepageHandler, name='home'),
]
main_app = airlock.WSGIApplication(routes)


api_app = service.service_mappings((
    ('/_api/assets.*', services.AssetService),
    ('/_api/admins.*', services.AdminService),
))


class RedirectMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'redirect_domain' in CONFIG:
            redirect_from = CONFIG['redirect_domain']['from']
            redirect_to = CONFIG['redirect_domain']['to']
            to_root = CONFIG['redirect_domain'].get('to_root')
            if redirect_from == os.getenv('HTTP_HOST', ''):
                status = '302 Found'
                if to_root:
                    url = redirect_to
                else:
                    url = redirect_to + os.getenv('PATH_INFO', '')
                response_headers = [('Location', url)]
                start_response(status, response_headers)
                return []
        if 'redirect_paths' in CONFIG:
            for path in CONFIG['redirect_paths']:
                if os.getenv('PATH_INFO', '') == path['from']:
                    status = '302 Found'
                    url = path['to']
                    response_headers = [('Location', url)]
                    start_response(status, response_headers)
                    return []
        return self.app(environ, start_response)


app = RedirectMiddleware(main_app)
