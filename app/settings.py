from . import messages
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import webapp2
import yaml


class Settings(ndb.Model):
  form = msgprop.MessageProperty(messages.SettingsMessage)

  @classmethod
  def singleton(cls):
    key = ndb.Key(cls.__name__, 'settings')
    ent = key.get()
    if ent is None:
      ent = cls(key=key)
      ent.put()
    return ent

  def to_fields(self):
    fields = []
    form = messages.SettingsFormMessage()
    for _, field in form.all_fields():
      fields.append({
          'name': field.name,
          'value': field.value,
      })
    return fields
