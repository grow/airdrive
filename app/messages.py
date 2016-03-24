from protorpc import messages
from protorpc import message_types


class Status(messages.Enum):
  NEW = 0
  PENDING = 1
  APPROVED = 2
  REJECTED = 3


class UserMessage(messages.Message):
  ident = messages.StringField(1)
  name = messages.StringField(2)
  email = messages.StringField(3)
  domain = messages.StringField(4)
  has_access = messages.BooleanField(5)
  status = messages.EnumField(Status, 6)


class FolderMessage(messages.Message):
  ident = messages.StringField(1)
  title = messages.StringField(2)
  color = messages.StringField(3)
  synced = message_types.DateTimeField(4)
  weight = messages.FloatField(5)
  edit_url = messages.StringField(6)
  sync_url = messages.StringField(7)
  url = messages.StringField(8)


class FoldersMessage(messages.Message):
  folders = messages.MessageField(FolderMessage, 1, repeated=True)


class ApprovalFormMessage(messages.Message):
  folders = messages.StringField(1, repeated=True)
  first_name = messages.StringField(2)
  last_name = messages.StringField(3)
  company_type = messages.StringField(4)
  job_title = messages.StringField(5)
  company = messages.StringField(6)
  region = messages.StringField(7)
  country = messages.StringField(8)
  justification = messages.StringField(10)
  email_opt_in = messages.BooleanField(11)
  company_email = messages.StringField(12)


class ApprovalMessage(messages.Message):
  created = message_types.DateTimeField(1)
  updated = message_types.DateTimeField(2)
  updated_by = messages.MessageField(UserMessage, 3)
  user = messages.MessageField(UserMessage, 4)
  form = messages.MessageField(ApprovalFormMessage, 5)
  status = messages.EnumField(Status, 6)
  ident = messages.StringField(7)


class ApprovalRequest(messages.Message):
  approval = messages.MessageField(ApprovalMessage, 1)


class ApprovalQueryMessage(messages.Message):
  cursor = messages.StringField(1)


class AdminMessage(messages.Message):
  email = messages.StringField(1)
  created = message_types.DateTimeField(2)
  created_by = messages.MessageField(UserMessage, 3)
  receives_email = messages.BooleanField(4)
  ident = messages.StringField(5)


class ApprovalsMessage(messages.Message):
  approvals = messages.MessageField(ApprovalMessage, 1, repeated=True)


class AdminsMessage(messages.Message):
  admins = messages.MessageField(AdminMessage, 1, repeated=True)


class UsersMessage(messages.Message):
  users = messages.MessageField(UserMessage, 1, repeated=True)


class SettingsFormMessage(messages.Message):
  content = messages.StringField(1)
  service_account = messages.StringField(2)
  root_folder = messages.StringField(3)
  api_key = messages.StringField(4)
  allow_gmail_accounts = messages.BooleanField(5)
  domain = messages.StringField(6)
  title = messages.StringField(7)
  sidebar_title = messages.StringField(8)
  sidebar_text = messages.StringField(9)
  email_footer = messages.StringField(10)
  logo_url = messages.StringField(11)
  email_logo_url = messages.StringField(12)
  contact_url = messages.StringField(13)


class SettingsMessage(messages.Message):
  form = messages.MessageField(SettingsFormMessage, 1)
