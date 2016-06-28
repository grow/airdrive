import json
import six
from protorpc import protojson
from protorpc import messages as protorpc_messages


class MessageJSONEncoder(json.JSONEncoder):
  """Message JSON encoder class.
  Extension of JSONEncoder that can build JSON from a message object.
  """

  def __init__(self, protojson_protocol=None, **kwargs):
    """Constructor.
    Args:
      protojson_protocol: ProtoJson instance.
    """
    super(MessageJSONEncoder, self).__init__(**kwargs)
    self.__protojson_protocol = protojson_protocol or protojson.ProtoJson.get_default()

  def default(self, value):
    """Return dictionary instance from a message object.
    Args:
    value: Value to get dictionary for.  If not encodable, will
      call superclasses default method.
    """
    if isinstance(value, protorpc_messages.Enum):
      return str(value)

    if six.PY3 and isinstance(value, bytes):
      return value.decode('utf8')

    if isinstance(value, protorpc_messages.Message):
      result = {}
      for field in value.all_fields():
        item = value.get_assigned_value(field.name)
        result[field.name] = self.__protojson_protocol.encode_field(
           field, item)
      # Handle unrecognized fields, so they're included when a message is
      # decoded then encoded.
      for unknown_key in value.all_unrecognized_fields():
        unrecognized_field, _ = value.get_unrecognized_field_info(unknown_key)
        result[unknown_key] = unrecognized_field
      return result
    else:
      return super(MessageJSONEncoder, self).default(value)


def patch():
  protojson.MessageJSONEncoder = MessageJSONEncoder
