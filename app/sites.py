from google.appengine.ext import ndb
from . import models


class Site(models.Model):
  root_folder_id = ndb.StringProperty()
  site_title = ndb.StringProperty()
  logo_url = ndb.StringProperty()
  email_footer = ndb.TextProperty()
  sidebar = ndb.StringProperty()
  path = ndb.StringProperty()
