from . import messages
from . import models
from . import approvals
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import airlock
import appengine_config


class User(models.Model, airlock.User):
  email = ndb.StringProperty()
  _message_class = messages.UserMessage

  @property
  def domain(self):
    if self.email:
      return self.email.split('@')[-1]

  def update(self, message, fields=None, put=True):
    self.name = message.name
    self.email = message.email
    if put:
      self.put()
    return self

  def to_message(self):
    message = self._message_class()
    message.ident = self.ident
    message.email = self.email
    message.domain = self.domain
    message.has_access = self.has_access
    message.status = self.status
    return message

  def list_approved_folders(self):
    return approvals.Approval.list_approved_folders_for_user(self)

  @property
  def has_access(self):
    if self.is_domain_user:
      return True
    return approvals.Approval.user_has_access(self)

  @property
  def status(self):
    status = None
    ent = approvals.Approval.get(self)
    if ent:
      status = ent.status
    return status or messages.Status.NEW

  @property
  def is_domain_user(self):
    return self.domain == appengine_config.CONFIG['domain']

  def has_access_to_folder(self, folder):
    if self.is_domain_user:
      return True
    return folder in self.list_approved_folders()
