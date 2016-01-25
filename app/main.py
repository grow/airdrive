import webapp2
from . import handlers


routes = [
    ('/sync/(.*)', handlers.SyncHandler),
    ('/sync', handlers.SyncHandler),
    ('/([^/]*)/folders/([^/]*)/', handlers.FolderHandler),
    ('/([^/]*)/([^/]*)/([^/]*)/', handlers.PageHandler),
    ('/([^/]*)/', handlers.MainFolderHandler),
]
app = webapp2.WSGIApplication(routes)
