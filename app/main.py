import webapp2
from . import handlers


routes = [
    ('/sync', handlers.SyncHandler),
]
app = webapp2.WSGIApplication(routes)
