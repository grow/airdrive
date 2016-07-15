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
  resource_id = messages.StringField(9)
  draft = messages.BooleanField(10)
  hidden = messages.BooleanField(11)


class AssetMetadata(messages.Message):
  width = messages.IntegerField(1)
  height = messages.IntegerField(2)
  language = messages.StringField(3)
  label = messages.StringField(4)
  dimensions = messages.StringField(5)
  ext = messages.StringField(6)
  base = messages.StringField(7)


class AssetMessage(messages.Message):
  ident = messages.StringField(1)
  download_url = messages.StringField(2)
  title = messages.StringField(3)
  size = messages.IntegerField(4)
  thumbnail_url = messages.StringField(8)
  metadata = messages.MessageField(AssetMetadata, 9)


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
  domain = messages.StringField(8)


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
  send_email = messages.BooleanField(2)
  cursor = messages.StringField(3)
  has_more = messages.BooleanField(4)


class AdminsMessage(messages.Message):
  admins = messages.MessageField(AdminMessage, 1, repeated=True)


class UsersMessage(messages.Message):
  users = messages.MessageField(UserMessage, 1, repeated=True)


class DirectlyAddUsersMessage(messages.Message):
  users = messages.MessageField(UserMessage, 1, repeated=True)
  send_email = messages.BooleanField(2)


class SettingsMessage(messages.Message):
  title = messages.StringField(7)
  sidebar_text = messages.StringField(9)
  email_footer = messages.StringField(10)
  logo_url = messages.StringField(11)
  contact_url = messages.StringField(13)
  interstitial = messages.StringField(17)
  color = messages.StringField(18)
  favicon_url = messages.StringField(19)
  interstitial_gmail_accounts = messages.StringField(21)
  google_analytics_id = messages.StringField(22)
  theme = messages.StringField(23)
  text_color = messages.StringField(24)
  text_on_brand_color = messages.StringField(25)
  keep_folders_open = messages.StringField(26)
  allow_gmail_accounts = messages.StringField(27)
  disable_domain_access = messages.StringField(28)


class ResourceMessage(messages.Message):
  resource_id = messages.StringField(1)


class ResourcesMessage(messages.Message):
  resource = messages.MessageField(ResourceMessage, 1)


class SyncMessage(messages.Message):
  resources = messages.MessageField(ResourceMessage, 1, repeated=True)
  token = messages.StringField(2)


class GetAssetGroupRequest(messages.Message):
  title = messages.StringField(1)
  parent_key = messages.StringField(2)


class GetAssetGroupResponse(messages.Message):
  assets = messages.MessageField(AssetMessage, 1, repeated=True)
  folder = messages.MessageField(FolderMessage, 2)
