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


class ApprovalQueryMessage(messages.Message):
  cursor = messages.StringField(1)
