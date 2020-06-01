from .base import *
SETTING_DEV_DIC = load_credential("develop")
SECRET_KEY = SETTING_DEV_DIC['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': SETTING_DEV_DIC["default"]
}

# # AWS
AWS_ACCESS_KEY_ID = SETTING_DEV_DIC['S3']['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = SETTING_DEV_DIC['S3']['AWS_SECRET_ACCESS_KEY']
AWS_DEFAULT_ACL = SETTING_DEV_DIC['S3']['AWS_DEFAULT_ACL']
AWS_S3_REGION_NAME = SETTING_DEV_DIC['S3']['AWS_S3_REGION_NAME']
AWS_S3_SIGNATURE_VERSION = SETTING_DEV_DIC['S3']['AWS_S3_SIGNATURE_VERSION']
AWS_STORAGE_BUCKET_NAME = SETTING_DEV_DIC['S3']['AWS_STORAGE_BUCKET_NAME']

AWS_QUERYSTRING_AUTH = False
AWS_S3_HOST = 's3.%s.amazonaws.com' % AWS_S3_REGION_NAME

AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)

STATIC_LOCATION = 'static'
STATIC_URL = "https://%s/%s/" % (AWS_S3_HOST, STATIC_LOCATION)
STATICFILES_STORAGE = 'siiot.storage.StaticStorage'

MEDIA_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_HOST, MEDIA_LOCATION)

DEFAULT_FILE_STORAGE = 'siiot.storage.CustomS3Boto3Storage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = "https://%s/static/" % AWS_S3_CUSTOM_DOMAIN
MEDIA_ROOT = "https://%s/media/" % AWS_S3_CUSTOM_DOMAIN

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "landing", "static"),
)


# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True

# # logging
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#         }
#     },
#     'loggers': {
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#         },
#     }
# }