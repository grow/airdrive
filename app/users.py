from . import approvals
from . import emails as emails_lib
from . import messages
from . import models
from email import utils as email_utils
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
import airlock
import appengine_config
import csv
import io
import logging
import webapp2


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

  @webapp2.cached_property
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

  def has_access_to_folder(self, resource_id):
    if self.is_domain_user:
      return True
    approved_folder_ids = self.list_approved_folders
    return resource_id in approved_folder_ids

  @classmethod
  def direct_add_users(cls, emails, created_by=None, send_email=False):
    approval_ents = []
    for email in emails:
      user_ent = cls.get_or_create_by_email(email)
      approval_form_message = messages.ApprovalFormMessage()
      approval_ent = approvals.Approval.create_and_approve(
          approval_form_message,
          user_ent,
          created_by=created_by)
      approval_ents.append(approval_ent)
      if send_email:
        emailer = emails_lib.Emailer(approval_ent)
        emailer.send_approved_to_user()
    return approval_ents

  @classmethod
  def parse_email(cls, email):
      return email_utils.parseaddr(email)[1]

  @classmethod
  def import_from_csv(cls, content, updated_by):
    fp = io.BytesIO()
    fp.write(content)
    fp.seek(0)
    reader = csv.DictReader(fp)
    ents = []
    for row in reader:
      valid_keys = []
      if 'email' not in row:
          raise Exception('Email not found.')
      email = cls.parse_email(row.pop('email', ''))
      for key in row.keys():
          if key in dir(messages.ApprovalFormMessage):
            valid_keys.append(key)
          else:
            del row[key]
      form = messages.ApprovalFormMessage(**row)
      user = cls.get_or_create_by_email(email)
      ent = approvals.Approval(
          user_key=user.key, form=form, updated_by_key=updated_by.key,
          status=messages.Status.APPROVED)
      ents.append(ent)
    return ents
