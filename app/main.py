import webapp2
from . import handlers


routes = [
    ('/sync', handlers.SyncHandler),
    ('/([^/]*)/folders/([^/]*)/', handlers.FolderHandler),
    ('/([^/]*)/([^/]*)/([^/]*)/', handlers.PageHandler),
]
app = webapp2.WSGIApplication(routes)
