# Django settings for Avatar project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'avatar'             # Or path to database file if using sqlite3.
DATABASE_USER = 'admin'             # Not used with sqlite3.
DATABASE_PASSWORD = '123456'         # Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = '3306'             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'
LANGUAGE_CODE = 'zh-cn'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = ''
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'p^r7bgf*-2j*l++=39l*w-b$w)9t!v5@*z-l9&v!x&lq$u6+3t'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'Avatar.utils.ExteriorAuthMiddlewares.ExteriorAuthMiddlewares',
    'Avatar.utils.SetRemoteAddrFromForwardedFor.SetRemoteAddrFromForwardedFor',
)
ROOT_URLCONF = 'Avatar.urls'

import logging,os
logging.basicConfig(  
   level = logging.DEBUG, 
   format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d %(message)s',  
   filename = 'syslog.log',  
)
TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__),"templates"), 
#    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)
STATIC_PATH = os.path.join(os.path.dirname(__file__),"site_media").replace('\\','/')


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'Avatar.snapshot',
)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
