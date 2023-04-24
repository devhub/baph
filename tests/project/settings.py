# Django settings for project project.

from __future__ import absolute_import
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        # Add 'postgresql', 'mssql', 'mysql', 'firebird', 'sqlite' or 'oracle'.
        'ENGINE': 'sqlite',
        # Or path to database file if using sqlite.
        'NAME': '/tmp/test-baph.db',
        # Not used with sqlite.
        'USER': '',
        # Not used with sqlite.
        'PASSWORD': '',
        # Set to empty string for localhost. Not used with sqlite.
        'HOST': '',
        # Set to empty string for default. Not used with sqlite.
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'pj&u&&p*%h7rdweo#7jpwj5oia3)4ll!nj9hrc+@pvez(o@f5w'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'baph.middleware.ssl.SSLRedirect',
    'baph.middleware.orm.SQLAlchemyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'baph.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'project.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
)

INSTALLED_APPS = (
    'baph.auth',
    'baph.auth.registration',
    'baph.db',
    'baph.piston',
    'baph.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

AUTHENTICATION_BACKENDS = (
    'baph.auth.backends.SQLAlchemyBackend',
)

# The length of the email field.
EMAIL_FIELD_LENGTH = 75

# for the SSL middleware
SSL_DOMAINS = [
]

# Amazon S3 config, example key values from:
# http://docs.amazonwebservices.com/AmazonS3/dev/S3_Authentication.html
AWS_ACCESS_KEY_ID = '022QF06E7MXBSH9DHM02'
AWS_SECRET_ACCESS_KEY = 'kWcrlUX5JEDGM/LtmEENI/aVmYvHNif5zB+d9+ct'
