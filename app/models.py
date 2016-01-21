from google.appengine.ext import ndb


class Model(ndb.Model):

  @classmethod
  def get(cls, ident):
    key = ndb.Key(cls.__name__, ident)
    return key.get()

  @classmethod
  def get_or_instantiate(cls, ident):
    ent = cls.get(ident)
    if ent is None:
      key = ndb.Key(cls.__name__, ident)
      ent = cls(key=key)
    return ent
