from .base import *
SETTING_STAG_DIC = load_credential("stagging")
SECRET_KEY = SETTING_STAG_DIC['SECRET_KEY']

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', '13.125.84.188', '15.164.101.147']

DATABASES = {
    'default': SETTING_STAG_DIC["default"],
    'bengal': load_credential('BENGAL_DATABASE'),
}


# AWS
AWS_ACCESS_KEY_ID = SETTING_STAG_DIC['S3']['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = SETTING_STAG_DIC['S3']['AWS_SECRET_ACCESS_KEY']
AWS_DEFAULT_ACL = SETTING_STAG_DIC['S3']['AWS_DEFAULT_ACL']
AWS_S3_REGION_NAME = SETTING_STAG_DIC['S3']['AWS_S3_REGION_NAME']
AWS_S3_SIGNATURE_VERSION = SETTING_STAG_DIC['S3']['AWS_S3_SIGNATURE_VERSION']
AWS_STORAGE_BUCKET_NAME = SETTING_STAG_DIC['S3']['AWS_STORAGE_BUCKET_NAME']

AWS_QUERYSTRING_AUTH = False
AWS_S3_HOST = 's3.%s.amazonaws.com' % AWS_S3_REGION_NAME

AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)

STATIC_LOCATION = 'statics'
STATIC_URL = "https://%s/%s/" % (AWS_S3_HOST, STATIC_LOCATION)
STATICFILES_STORAGE = 'pepup.storage.StaticStorage'

MEDIA_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_HOST, MEDIA_LOCATION)
DEFAULT_FILE_STORAGE = 'pepup.storage.MediaStorage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = "https://%s/statics/" % AWS_S3_CUSTOM_DOMAIN
MEDIA_ROOT = "https://%s/media/" % AWS_S3_CUSTOM_DOMAIN
