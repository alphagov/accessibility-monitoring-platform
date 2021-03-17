"""
Django settings for accessibility_monitoring_platform project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import dj_database_url
import os
import json
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv('DEBUG') == 'TRUE' else False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')

# Application definition

INSTALLED_APPS = [
    'accessibility_monitoring_platform.apps.dashboard',
    'accessibility_monitoring_platform.apps.query_local_website_registry',
    'accessibility_monitoring_platform.apps.users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'accessibility_monitoring_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'accessibility_monitoring_platform/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

json_acceptable_string = os.getenv('VCAP_SERVICES').replace("'", "\"")
d = json.loads(json_acceptable_string)

DATABASES = {}
DATABASES['default'] = dj_database_url.parse(d['postgres'][0]['credentials']['uri'])
DATABASES['accessibility_domain_db'] = dj_database_url.parse(d['postgres'][1]['credentials']['uri'])
DATABASES['accessibility_domain_db']['OPTIONS'] = {'options': '-c search_path=pubsecweb,public'}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


LOGIN_REDIRECT_URL = 'dashboard:home'

LOGOUT_REDIRECT_URL = 'dashboard:home'
if os.getenv('EMAIL_BACKEND'):
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = os.getenv('EMAIL_PORT')
else:
    EMAIL_BACKEND = 'accessibility_monitoring_platform.email.NotifyEmailBackend'
    EMAIL_NOTIFY_API_KEY = os.getenv('EMAIL_NOTIFY_API_KEY')
    EMAIL_NOTIFY_BASIC_TEMPLATE = os.getenv('EMAIL_NOTIFY_BASIC_TEMPLATE')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
)

STATICFILES_DIRS = [
    BASE_DIR / 'accessibility_monitoring_platform/static/compiled/'
]

# Needed for deployment
STATIC_URL = os.path.join(BASE_DIR, '/static/')
# accessibility_monitoring_platform/static/dist/css/init.css

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static/dist')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
