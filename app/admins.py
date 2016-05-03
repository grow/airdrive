from . import messages
from . import models
from google.appengine.ext import ndb
import appengine_config


class Admin(models.Model):
  email = ndb.StringProperty()
  created = ndb.DateTimeProperty(auto_now_add=True)
  created_by_key = ndb.KeyProperty()
  receives_email = ndb.BooleanProperty(default=False)

  @classmethod
  def is_admin(cls, email):
    if email in appengine_config.CONFIG['admins']:
      return True
    return cls.get_by_email(email)

  @classmethod
  def list_emails(cls):
    emails = []
    for admin in cls.list():
      if admin.receives_email:
        emails.append(admin.email)
    return emails

  @classmethod
  def create_multi(cls, messages, created_by):
    created = []
    for message in messages:
      ent = cls.create(message.email, created_by=created_by)
      created.append(ent)
    return created

  @classmethod
  def create(cls, email, created_by):
    existing = cls.get_by_email(email)
    if existing:
      return existing
    ent = cls(id=email)
    ent.email = email
    ent.created_by_key = created_by.key
    ent.put()
    return ent

  def update(self, message):
    self.receives_email = message.receives_email
    self.put()

  @classmethod
  def list(cls):
    query = cls.query()
    query = query.order(-cls.created)
    return query.fetch()

  @classmethod
  def get_by_email(cls, email):
    return cls.get_by_id(email)

  def to_message(self):
    message = messages.AdminMessage()
    message.email = self.email
    message.created = self.created
    if self.created_by:
        message.created_by = self.created_by.to_message()
    message.receives_email = self.receives_email
    message.ident = self.ident
    return message
