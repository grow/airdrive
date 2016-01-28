from . import handlers
import airlock
import appengine_config
import webapp2

airlock.set_config(appengine_config.AIRLOCK_CONFIG)

routes = [
    webapp2.Route('/sync/<resource_id>/', handlers.SyncHandler),
    webapp2.Route('/sync/', handlers.SyncHandler, name='sync'),
    webapp2.Route('/assets/<resource_id>', handlers.AssetDownloadHandler, name='asset'),
    webapp2.Route('/settings/', handlers.SettingsHandler, name='settings'),
    webapp2.Route('/admin/approvals/<ident>/', handlers.AdminApprovalsApprovalHandler, name='admin-approvals-approval'),
    webapp2.Route('/admin/<template>/', handlers.AdminHandler, name='admin-page'),
    webapp2.Route('/admin/', handlers.AdminHandler, name='admin'),
    webapp2.Route('/<folder_slug>/folders/<resource_id>/', handlers.FolderHandler),
    webapp2.Route('/<folder_slug>/<resource_id>/<page_slug>/', handlers.PageHandler),
    webapp2.Route('/<folder_slug>/', handlers.MainFolderHandler, name='main-folder'),
    webapp2.Route('/', handlers.HomepageHandler, name='home'),
]
app = airlock.WSGIApplication(routes)
