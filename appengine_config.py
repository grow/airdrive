import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from airlock import config as airlock_config
import json
import mimetypes
import yaml

DEV_SERVER = os.getenv('SERVER_SOFTWARE').startswith('Dev')
OFFLINE = False

CONFIG = yaml.load(open(os.getenv('AIRPRESS_CONFIG')))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config')

VERSION = os.getenv('CURRENT_VERSION_ID')

DEFAULT_THEME = 'material'

from google.appengine.api import app_identity
APP_SERVICE_ACCOUNT = app_identity.get_service_account_name()

_appid = os.getenv('APPLICATION_ID').replace('s~', '')
EMAIL_SENDER = 'noreply@{}.appspotmail.com'.format(_appid)
BASE_URL = '{}://{}'.format(
    os.getenv('wsgi.url_scheme'), os.getenv('SERVER_NAME'))

mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('font/opentype', '.otf')
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('font/woff', '.woff')

_client_secrets_basename = CONFIG['client_secrets']
_client_secrets_path = os.path.join(CONFIG_PATH, _client_secrets_basename)
_client_secrets = json.load(open(_client_secrets_path))

AIRLOCK_CONFIG = {
    'client_secrets_path': _client_secrets_path,
    'webapp2_extras.auth': {
        'token_cache_age': airlock_config.Defaults.Xsrf.TOKEN_AGE,
        'token_max_age': airlock_config.Defaults.Xsrf.TOKEN_AGE,
        'token_new_age': airlock_config.Defaults.Xsrf.TOKEN_AGE,
        'user_model': 'app.users.User',
    },
    'webapp2_extras.sessions': {
        'secret_key': str(_client_secrets['web']['client_secret']),
        'user_model': 'app.users.User',
    },
}
