import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import mimetypes
import yaml

CONFIG = yaml.load(open('config/config.yaml'))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config')

VERSION = os.getenv('CURRENT_VERSION_ID')

_appid = os.getenv('APPLICATION_ID').replace('s~', '')
EMAIL_SENDER = 'noreply@{}.appspotmail.com'.format(_appid)
BASE_URL = '{}://{}'.format(os.getenv('wsgi.url_scheme'), os.getenv('SERVER_NAME'))

mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('font/opentype', '.otf')
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('font/woff', '.woff')
