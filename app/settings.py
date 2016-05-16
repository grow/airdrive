from . import messages
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import webapp2
import yaml


class Settings(ndb.Model):
  form = msgprop.MessageProperty(
      messages.SettingsMessage, default=messages.SettingsMessage())

  @classmethod
  def singleton(cls):
    key = ndb.Key(cls.__name__, 'settings')
    ent = key.get()
    if ent is None:
      ent = cls(key=key)
      ent.form = messages.SettingsMessage()
      ent.put()
    return ent

  def update(self, message):
    self.form = message
    self.put()
    return self

  def get_form(self):
    return self.form or messages.SettingsMessage()

  @property
  def fields(self):
    if self.form:
      return self.form.all_fields()
    form = messages.SettingsMessage()
    return form.all_fields()
