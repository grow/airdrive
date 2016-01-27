import webapp2
from . import handlers


routes = [
    webapp2.Route('/sync/<resource_id>', handlers.SyncHandler),
    webapp2.Route('/sync', handlers.SyncHandler),
    webapp2.Route('/<folder_slug>/folders/<resource_id>/', handlers.FolderHandler),
    webapp2.Route('/<folder_slug>/<resource_id>/<page_slug>/', handlers.PageHandler),
    webapp2.Route('/<folder_slug>/', handlers.MainFolderHandler, name='main-folder'),
    webapp2.Route('/assets/<resource_id>', handlers.AssetDownloadHandler, name='asset'),
    webapp2.Route('/settings', handlers.SettingsHandler, name='settings'),
    webapp2.Route('/', handlers.HomepageHandler, name='home'),
]
app = webapp2.WSGIApplication(routes)
