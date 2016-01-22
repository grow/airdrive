from . import folders
from . import sync
import jinja2
import os
import webapp2


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Handler(webapp2.RequestHandler):
  pass


class SyncHandler(Handler):

  def get(self):
    resource_id = '0BzZ9lY-SjtYab1ZrY2Y0d085dkU'
    resp = sync.download_resource(resource_id)
    folder = folders.Folder.get(resource_id)
    children = folder.list_children()
    self.response.out.write(children)
