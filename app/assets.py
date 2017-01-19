# coding=utf-8
from . import messages
from . import models
from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from google.appengine.ext import blobstore
import appengine_config
import datetime
import os
import re
import webapp2

DOWNLOAD_URL_FORMAT = 'https://www.googleapis.com/drive/v3/files/{resource_id}?alt=media&key={key}'

THUMBNAIL_URL_FORMAT = 'https://drive.google.com/thumbnail?sz=w{size}&id={resource_id}'

CONFIG = appengine_config.CONFIG

VARIANT_IDENTIFIERS = (
    ('_STD_', 'Standard'),
    ('_DBS_', 'Double-sided'),
    ('_SGS_', 'Single-sided'),
    ('_15A_', '15 degree angle'),
    ('_30A_', '30 degree angle'),
)

MESSAGING_IDENTIFIERS = (
    ('_ALL_', 'All'),
    ('_CIRCULAR_', 'Circular'),
    ('_CO-BRAND_', 'Co-branding'),
    ('_CTA_', 'Call-to-action'),
    ('_MAPS_', 'Maps'),
    ('_MUSIC_', 'Music'),
    ('_PHOTOS_', 'Photos'),
    ('_PROMO_', 'Promotional'),
    ('_PROMOV1_', 'Promotional Single'),
    ('_PROMOV2_', 'Promotional Lifestyle'),
    ('_PROMOV3_', 'Promotional Multipack'),
    ('_SEARCH_', 'Search'),
    ('_SOCIALMEDIA_', 'Social media'),
    ('_STANDALONE_', 'Standalone'),
    ('_STD_', 'Standard'),
    ('_STDV1_', 'Standard Single'),
    ('_STDV2_', 'Standard Device'),
    ('_STDV3_', 'Standard Multipack'),
    ('_YOUTUBE_', 'YouTube'),
    ('CC_CC4K_CCA_', 'Chromecast, Chromecast Ultra & Chromecast Audio'),
    ('CC_CC4K_', 'Chromecast & Chromecast Ultra'),
    ('CC_CCA_', 'Chromecast & Chromecast Audio'),
    ('CC_', 'Chromecast'),
    ('CC4K_', 'Chromecast Ultra'),
    ('CCA_', 'Chromecast Audio'),
)

FILENAME_IDENTIFIERS_TO_LOCALES = {
    '_AF_': 'af',
    '_AR-AE_': 'ar-ae',
    '_AR-BH_': 'ar-bh',
    '_AR-DZ_': 'ar-dz',
    '_AR-EG_': 'ar-eg',
    '_AR-IQ_': 'ar-iq',
    '_AR-JO_': 'ar-jo',
    '_AR-KW_': 'ar-kw',
    '_AR-LB_': 'ar-lb',
    '_AR-LY_': 'ar-ly',
    '_AR-MA_': 'ar-ma',
    '_AR-OM_': 'ar-om',
    '_AR-QA_': 'ar-qa',
    '_AR-SA_': 'ar-sa',
    '_AR-SY_': 'ar-sy',
    '_AR-TN_': 'ar-tn',
    '_AR-YE_': 'ar-ye',
    '_AR_': 'ar',
    '_BE_': 'be',
    '_BG_': 'bg',
    '_CA_': 'ca',
    '_CS_': 'cs',
    '_CY_': 'cy',
    '_DA_': 'da',
    '_DK_': 'da',
    '_DE-AT_': 'de-at',
    '_DE-CH_': 'de-ch',
    '_DE-LI_': 'de-li',
    '_DE-LU_': 'de-lu',
    '_DE_': 'de',
    '_DE_': 'de',
    '_DE_': 'de',
    '_EL_': 'el',
    '_EN_AU_': 'en-au',
    '_EN_BZ_': 'en-bz',
    '_EN_CA_': 'en-ca',
    '_EN_GB_': 'en-gb',
    '_EN_IE_': 'en-ie',
    '_EN_IN_': 'en-in',
    '_EN_JM_': 'en-jm',
    '_EN_NZ_': 'en-nz',
    '_EN_TT_': 'en-tt',
    '_EN_US_': 'en-us',
    '_EN_ZA_': 'en-za',
    '_EN_': 'en',
    '_ES-AR_': 'es-ar',
    '_ES-BO_': 'es-bo',
    '_ES-CL_': 'es-cl',
    '_ES-CO_': 'es-co',
    '_ES-CR_': 'es-cr',
    '_ES-DO_': 'es-do',
    '_ES-EC_': 'es-ec',
    '_ES-GT_': 'es-gt',
    '_ES-HN_': 'es-hn',
    '_ES-MX_': 'es-mx',
    '_ES-NI_': 'es-ni',
    '_ES-PA_': 'es-pa',
    '_ES-PE_': 'es-pe',
    '_ES-PR_': 'es-pr',
    '_ES-PY_': 'es-py',
    '_ES-SV_': 'es-sv',
    '_ES-UY_': 'es-uy',
    '_ES-VE_': 'es-ve',
    '_ES_': 'es',
    '_ES_': 'es',
    '_ET_': 'et',
    '_EU_': 'eu',
    '_FA_': 'fa',
    '_FI_': 'fi',
    '_FO_': 'fo',
    '_FR_BE_': 'fr-be',
    '_FR_CA_': 'fr-ca',
    '_FR_CH_': 'fr-ch',
    '_FR_LU_': 'fr-lu',
    '_FR_': 'fr',
    '_FR_': 'fr',
    '_GA_': 'ga',
    '_GD_': 'gd',
    '_HE_': 'he',
    '_HI_': 'hi',
    '_HR_': 'hr',
    '_HU_': 'hu',
    '_ID_': 'id',
    '_IS_': 'is',
    '_IT-CH_': 'it-ch',
    '_IT_': 'it',
    '_IT_': 'it',
    '_JA_': 'ja',
    '_JP_': 'ja',
    '_JI_': 'ji',
    '_KO_': 'ko',
    '_KO_': 'ko',
    '_KO_': 'ko',
    '_KU_': 'ku',
    '_LT_': 'lt',
    '_LV_': 'lv',
    '_MK_': 'mk',
    '_ML_': 'ml',
    '_MS_': 'ms',
    '_MT_': 'mt',
    '_NB_': 'nb',
    '_NL-BE_': 'nl-be',
    '_NL_': 'nl',
    '_NL_': 'nl',
    '_NN_': 'nn',
    '_NO_': 'no',
    '_PA_': 'pa',
    '_PL_': 'pl',
    '_PL_': 'pl',
    '_PT-BR_': 'pt-br',
    '_PT_': 'pt',
    '_PT_': 'pt',
    '_RM_': 'rm',
    '_RO-MD_': 'ro-md',
    '_RO_': 'ro',
    '_RU-MD_': 'ru-md',
    '_RU_': 'ru',
    '_RU_': 'ru',
    '_SB_': 'sb',
    '_SK_': 'sk',
    '_SL_': 'sl',
    '_SQ_': 'sq',
    '_SR_': 'sr',
    '_SV-FI_': 'sv-fi',
    '_SV_': 'sv',
    '_SE_': 'sv',
    '_TH_': 'th',
    '_TH_': 'th',
    '_TN_': 'tn',
    '_TR_': 'tr',
    '_TR_': 'tr',
    '_TS_': 'ts',
    '_UK_': 'uk',
    '_UR_': 'ur',
    '_VE_': 've',
    '_VI_': 'vi',
    '_XH_': 'xh',
    '_ZH-CN_': 'zh-cn',
    '_ZH-CN_': 'zh-cn',
    '_ZH-HK_': 'zh-hk',
    '_ZH-SG_': 'zh-sg',
    '_ZH-TW_': 'zh-tw',
    '_ZH-TW_': 'zh-tw',
    '_ZU_': 'zu',
}


class Asset(models.BaseResourceModel):
  size = ndb.IntegerProperty()
  build = ndb.IntegerProperty()
  mimetype = ndb.StringProperty()
  md5 = ndb.StringProperty()
  parents = ndb.KeyProperty(repeated=True)
  basename = ndb.StringProperty()
  ext = ndb.StringProperty()
  url = ndb.StringProperty()
  icon_url = ndb.StringProperty()
  num_downloads = ndb.IntegerProperty(default=0)
  gcs_path = ndb.StringProperty()
  gcs_thumbnail_path = ndb.StringProperty()
  etag = ndb.StringProperty()
  metadata = msgprop.MessageProperty(
      messages.AssetMetadata, indexed_fields=['width', 'height', 'label'])

  @classmethod
  def process(cls, resp, gcs_path=None, gcs_thumbnail_path=None):
    if '.preview' in resp['title']:  # Don't store previews.
      return
    resource_id = resp['id']
    ent = cls.get_or_instantiate(resource_id)
    ent.resource_id = resource_id
    ent.mimetype = resp['mimeType']
    ent.size = int(resp['fileSize'])
    ent.url = resp['webContentLink']
    ent.icon_url = resp['iconLink']
    ent.parse_title(resp['title'])
    ent.md5 = resp['md5Checksum']
    ent.etag = resp['etag']
    if gcs_path:
      ent.gcs_path = gcs_path
    if gcs_thumbnail_path:
      ent.gcs_thumbnail_path = gcs_thumbnail_path
    ent.modified = cls.parse_datetime_string(resp['modifiedDate'])
    ent.synced = datetime.datetime.now()
    ent.parents = cls.generate_parent_keys(resp['parents'])
    ent.basename, ent.ext = os.path.splitext(resp['title'])
    ent.set_metadata(resp)
    ent.put()

  @classmethod
  def get_group(cls, parent_key=None):
    query = cls.query()
    query = query.filter(cls.parents == parent_key)
    ents = query.fetch()
    asset_messages = [ent.to_message() for ent in ents]
    for message in asset_messages:
      if message.metadata and not message.metadata.label:
        message.metadata.label = 'Standard'
    folder = parent_key.get()
    if folder:
        folder_message = folder.to_message()
    else:
        folder_message = None
    return folder_message, asset_messages

  @classmethod
  def get_by_basename(cls, basename):
    query = cls.query()
    query = query.filter(cls.basename == basename)
    return query.get()

  def set_metadata(self, resp):
    metadata = messages.AssetMetadata()
    # Formatted: CB_US_STD_ATTRACT_HANGING_LANDSCAPE_48x24.ext
    title = resp['title']
    base, ext = os.path.splitext(resp['title'])
    metadata.base = base
    metadata.ext = ext

    # Language.
    for key, value in FILENAME_IDENTIFIERS_TO_LOCALES.iteritems():
        if key in base:
            metadata.language = value
            break

    # Variant.
    metadata.variant = 'Standard'
    for key, value in VARIANT_IDENTIFIERS:
        if key in base:
            metadata.variant = value
            break

    # Meassaging.
    metadata.label = 'Standard'
    for key, value in MESSAGING_IDENTIFIERS:
        if key in base:
            metadata.label = value
            break

    # Width and height.
    for part in base.split('_'):
      part = re.sub('[p][x]', '', part)
      match = re.match('(\d*)x(\d*)', part)
      if match:
        width, height = match.groups()
        if width and height:
            metadata.width = int(width)
            metadata.height = int(height)
            metadata.dimensions = '{}x{}'.format(width, height)

    self.metadata = metadata

  @property
  def media_url(self):
    return DOWNLOAD_URL_FORMAT.format(
        resource_id=self.resource_id,
        key=CONFIG['apikey'])

  @property
  def thumbnail_url(self):
    return '/thumbnails/{}'.format(self.resource_id)

  @classmethod
  def create_thumbnail_url(cls, resource_id):
    return THUMBNAIL_URL_FORMAT.format(
        resource_id=resource_id,
        size=250)

  @property
  def download_url(self):
    return '/assets/{}'.format(self.resource_id)

  @classmethod
  def search_by_downloads(cls):
    query = cls.query()
    query = query.filter(cls.num_downloads != 0)
    query = query.order(-cls.num_downloads)
    return query.fetch()

  @webapp2.cached_property
  def parent(self):
    if self.parents:
      return self.parents[0].get()

  def create_blob_key(self, thumbnail=False):
    if thumbnail:
      return blobstore.create_gs_key('/gs{}'.format(self.gcs_thumbnail_path))
    return blobstore.create_gs_key('/gs{}'.format(self.gcs_path))

  def to_message(self):
    message = messages.AssetMessage()
    message.ident = self.ident
    message.download_url = self.download_url
    message.title = self.title
    message.size = self.size
    message.thumbnail_url = self.thumbnail_url
    message.metadata = self.metadata
    message.has_thumbnail = bool(self.gcs_thumbnail_path)
    return message
