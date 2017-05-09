from . import admins
from . import approvals
from . import emails as emails_lib
from . import messages
from . import models
from . import settings
from . import sync
from email import utils as email_utils
from google.appengine.ext import ndb
from google.appengine.ext import deferred
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
    form = settings.Settings.singleton().form
    if self.is_domain_user and not form.disable_domain_access:
      return True
    if admins.Admin.is_admin(self.email):
      return True
    if form.public:
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
    options = settings.Settings.singleton()
    if hasattr(options, 'domain'):
        domain = options.domain or appengine_config.CONFIG.get('domain')
    else:
        domain = appengine_config.CONFIG.get('domain')
    return self.domain == domain

  def can_access_resource(self, resource):
    form = settings.Settings.singleton().form
    if self.is_domain_user or admins.Admin.is_admin(self.email):
      return True
    if form.public:
      return True
    item = resource
    approved_folder_ids = self.list_approved_folders
    while item:
      if item.is_public:
        return True
      if item.hidden or item.draft:
        return False
      if item.resource_id in approved_folder_ids:
        return True
      item = item.parent
    return False

  def has_access_to_folder(self, resource_id):
    form = settings.Settings.singleton().form
    if self.is_domain_user or admins.Admin.is_admin(self.email):
      return True
    if form.public:
      return True
    approved_folder_ids = self.list_approved_folders
    return resource_id in approved_folder_ids

  @classmethod
  def add_access(cls, emails, created_by, form):
    approval_ents = []
    for email in emails:
      user_ent = cls.get_or_create_by_email(email)
      approval_ent = approvals.Approval.get(user_ent)
      if not approval_ent:
        approval_ent = approvals.Approval.get_or_create(
              form=form,
              user=user_ent, created_by=created_by,
              status=messages.Status.APPROVED,
              send_email=False)
      approval_ent.add_folders(form.folders)
      approval_ents.append(approval_ent)
    return approval_ents

  @classmethod
  def remove_access(cls, emails, created_by, form):
    approval_ents = []
    for email in emails:
      user_ent = cls.get_or_create_by_email(email)
      approval_ent = approvals.Approval.get(user_ent)
      if not approval_ent:
        continue
      approval_ent.remove_folders(form.folders)
      approval_ents.append(approval_ent)
    return approval_ents

  @classmethod
  def direct_add_users(cls, emails, created_by=None, send_email=False, form=None):
    approval_ents = []
    for email in emails:
      user_ent = cls.get_or_create_by_email(email)
      form = form or messages.ApprovalFormMessage()
      approval_ent = approvals.Approval.create_and_approve(
          form,
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
  def _import(cls, row, form, created_by, send_email):
    valid_keys = []
    email = cls.parse_email(row.pop('email', ''))
    for key in row.keys():
        if key in dir(messages.ApprovalFormMessage):
          row[key] = row[key].decode('utf-8')
          valid_keys.append(key)
        else:
          del row[key]
    new_form = messages.ApprovalFormMessage(**row)
    if form:
      new_form.folders = form.folders
    user = cls.get_or_create_by_email(email)
    ent = approvals.Approval.get_or_create(
        form=new_form,
        user=user, created_by=created_by,
        status=messages.Status.APPROVED,
        send_email=send_email)

  @classmethod
  def import_from_csv(cls, content, form, created_by, send_email=False):
    fp = io.BytesIO()
    fp.write(content)
    fp.seek(0)
    reader = csv.DictReader(fp)
    for row in reader:
        if 'email' not in row:
            continue
        cls._import(row, form, created_by, send_email)

  @classmethod
  def import_from_google_sheets(cls, sheet_id, created_by, form=None, gid=None,
                                send_email=False):
    content = cls.download_from_google_sheets(sheet_id=sheet_id, gid=gid)
    return cls.import_from_csv(
        content,
        form=form,
        created_by=created_by,
        send_email=send_email)

  @classmethod
  def download_from_google_sheets(cls, sheet_id, gid=None):
    service = sync.service
    resp = service.files().get(fileId=sheet_id).execute()
    if 'exportLinks' not in resp:
      raise Exception('Nothing to export: {}'.format(sheet_id))
    for mimetype, url in resp['exportLinks'].iteritems():
        if not mimetype.endswith('csv'):
            continue
        if gid is not None:
            url += '&gid={}'.format(gid)
        resp, content = service._http.request(url)
        if resp.status != 200:
            text = 'Error {} downloading sheet: {}'
            text = text.format(resp.status, sheet_id)
            raise Exception(text)
        return content
