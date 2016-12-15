from . import messages
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import appengine_config
import webapp2
import yaml


CONFIG = appengine_config.CONFIG


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

  def get_theme(self):
    form = self.get_form()
    return form.theme \
        or appengine_config.CONFIG.get('theme') \
        or appengine_config.DEFAULT_THEME

  @property
  def theme(self):
    return self.get_theme()

  @property
  def title(self):
    form = self.get_form()
    return form.title or appengine_config.CONFIG.get('title', 'Toolkit')
