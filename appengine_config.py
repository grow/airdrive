import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

import yaml

CONFIG = yaml.load(open('config.yaml'))

VERSION = os.getenv('CURRENT_VERSION_ID')
