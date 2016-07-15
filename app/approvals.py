import airlock
from . import emails
from . import messages
from . import models
from google.appengine.datastore import datastore_query
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import protojson
import csv
import io
import json

PER_PAGE = 50


class User(models.Model, airlock.User):
  email = ndb.StringProperty()
  _message_class = messages.UserMessage

  def to_message(self):
    message = self._message_class()
    message.email = self.email
    return message


class Approval(models.BaseResourceModel):
  _message_class = messages.ApprovalMessage
  created = ndb.DateTimeProperty(auto_now_add=True)
  form = msgprop.MessageProperty(
      messages.ApprovalFormMessage, indexed_fields=['folders'])
  user_key = ndb.KeyProperty()
  user = ndb.StructuredProperty(User)
  domain = ndb.StringProperty()
  updated_by_key = ndb.KeyProperty()
  updated_by = ndb.StructuredProperty(User)
  status = msgprop.EnumProperty(messages.Status, default=messages.Status.PENDING)
  updated = ndb.DateTimeProperty(auto_now=True)

  _csv_header = [
      'company',
      'company_email',
      'company_type',
      'country',
      'email_opt_in',
      'first_name',
      'folders',
      'job_title',
      'justification',
      'last_name',
      'region',
  ]

  def to_message(self):
    message = self._message_class()
    message.created = self.created
    message.ident = self.ident
    if self.user:
        message.user = self.user.to_message()
    elif not self.user and self.user_key:
        ent = self.user_key.get()
        if ent:
            message.user = ent.to_message()
    message.status = self.status
    message.updated = self.updated
    message.form = self.form
    if self.updated_by:
      message.updated_by = self.updated_by.to_message()
    message.domain = self.domain
    return message

  @classmethod
  def get(cls, user):
    query = cls.query()
    query = query.filter(cls.user_key == user.key)
    return query.get()

  def update(self, message, updated_by):
    self.form = message.form
    if self.form.folders:
      self.form.folders = list(set(self.form.folders))
    embedded_user = User(**updated_by.to_dict())
    self.updated_by = embedded_user
    self.updated_by_key = updated_by.key
    self.put()
    return self

  @classmethod
  def get_or_create(cls, approval_form_message, user, send_email=True):
    ent = cls.get(user)
    if ent:
      return ent
    return cls.create(approval_form_message, user, send_email)

  @classmethod
  def create(cls, approval_form_message, user, email=True):
    embedded_user = User(**user.to_dict())
    ent = cls(user_key=user.key, user=embedded_user, form=approval_form_message)
    ent.put()
    if email:
      emailer = emails.Emailer(ent)
      emailer.send_created_to_user()
      emailer.send_created_to_admins()
    return ent

  @classmethod
  def create_and_approve(cls, message, user, created_by):
    ent = cls.get_or_create(message, user, send_email=False)
    ent.approve(created_by, email=False)
    return ent

  @classmethod
  def search(cls, cursor=None):
    start_cursor = datastore_query.Cursor(urlsafe=cursor) if cursor else None
    query = cls.query()
    query = query.order(-cls.created)
    results, next_cursor, has_more = query.fetch_page(
        PER_PAGE, start_cursor=start_cursor)
    return (results, next_cursor, has_more)

  def approve(self, updated_by, email=True):
    self.status = messages.Status.APPROVED
    embedded_user = User(**updated_by.to_dict())
    self.updated_by = embedded_user
    self.updated_by_key = updated_by.key
    self.put()
    if email:
      emailer = emails.Emailer(self)
      emailer.send_approved_to_user()

  def reject(self, updated_by, email=True):
    self.status = messages.Status.REJECTED
    embedded_user = User(**updated_by.to_dict())
    self.updated_by = embedded_user
    self.updated_by_key = updated_by.key
    self.put()
    if email:
      emailer = emails.Emailer(self)
      emailer.send_rejected_to_user()

  @classmethod
  def approve_multi(cls, approval_messages, updated_by, send_email=False):
    ents = cls.get_multi(approval_messages)
    for ent in ents:
      ent.approve(updated_by, email=send_email)
    return ents

  @classmethod
  def reject_multi(cls, approval_messages, updated_by, send_email=False):
    ents = cls.get_multi(approval_messages)
    for ent in ents:
      ent.reject(updated_by, email=send_email)
    return ents

  @classmethod
  def list_approvals_for_user(cls, user):
    query = cls.query()
    query = query.filter(cls.user_key == user.key)
    results = query.fetch()
    if results is None:
      return []
    return results

  @classmethod
  def list_approved_folders_for_user(cls, user):
    result = cls.get(user)
    approved_folders = set()
    if not result:
      return approved_folders
    if result.status != messages.Status.APPROVED:
      return approved_folders
    approved_folders |= set(result.form.folders)
    return approved_folders

  @classmethod
  def user_has_access(cls, user):
    ents = cls.list_approvals_for_user(user)
    for ent in ents:
      if ent.status == messages.Status.APPROVED:
        return True

  @property
  def serialized_form(self):
    return json.loads(protojson.encode_message(self.form))

  @classmethod
  def to_csv(cls):
    header = cls._csv_header
    ents, _, _ = cls.search()
    rows = []
    for ent in ents:
      ent.form = ent.form or messages.ApprovalFormMessage()
      encoded_form = json.loads(protojson.encode_message(ent.form))
      row = json.loads(protojson.encode_message(ent.to_message()))
      if 'email_opt_in' not in row:
        row['email_opt_in'] = False
      for key in row.keys():
        if key not in header:
          del row[key]
      row.update(encoded_form)
      for key in row:
        if isinstance(row[key], unicode):
          row[key] = row[key].encode('utf-8')
      rows.append(row)
    if not rows:
      return ''
    fp = io.BytesIO()
    writer = csv.DictWriter(fp, header)
    writer.writeheader()
    writer.writerows(rows)
    fp.seek(0)
    return fp.read()

  @classmethod
  def decode_form(cls, form_dict):
    encoded_message = json.dumps(form_dict)
    return protojson.decode_message(
        messages.ApprovalFormMessage,
        encoded_message)

  @classmethod
  def import_from_csv(cls, content, updated_by):
    fp = io.BytesIO()
    fp.write(content)
    fp.seek(0)
    reader = csv.DictReader(fp)
    ents = []
    for row in reader:
      form = messages.ApprovalFormMessage(**row)
      email = users.User.parse_email(row['email'])
      user = users.User.get_or_create_by_email(email)
      ent = cls(user=user, form=form, updated_by_key=updated_by.key,
                status=messages.Status.APPROVED)
      ents.append(ent)
    import logging
    logging.info(ents)
