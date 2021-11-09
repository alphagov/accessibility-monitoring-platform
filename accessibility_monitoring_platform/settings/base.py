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
import sys
import os
import json
from dotenv import load_dotenv

UNDER_TEST = len(sys.argv) > 1 and sys.argv[1] == "test"

if "pytest" in sys.modules:
    UNDER_TEST = True

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG") == "TRUE"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(" ")

# Application definition

INSTALLED_APPS = [
    "accessibility_monitoring_platform.apps.cases",
    "accessibility_monitoring_platform.apps.checks",
    "accessibility_monitoring_platform.apps.common",
    "accessibility_monitoring_platform.apps.dashboard",
    "accessibility_monitoring_platform.apps.users",
    "accessibility_monitoring_platform.apps.websites",
    "accessibility_monitoring_platform.apps.notifications",
    "accessibility_monitoring_platform.apps.comments",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "accessibility_monitoring_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accessibility_monitoring_platform.apps.common.context_processors.platform_page",
            ],
        },
    },
]


DATABASES = {}

if UNDER_TEST:
    DATABASES["default"] = {
        "NAME": "accessibility_monitoring_app",
        "ENGINE": "django.db.backends.sqlite3",
    }
    DATABASES["pubsecweb_db"] = {
        "NAME": "pubsecweb_db",
        "ENGINE": "django.db.backends.sqlite3",
    }
    DATABASES["a11ymon_db"] = {
        "NAME": "a11ymon_db",
        "ENGINE": "django.db.backends.sqlite3",
    }
else:
    DATABASE_SERVICE_NAMES = ["monitoring-platform-default-db", "a11ymon-postgres"]
    json_acceptable_string = os.getenv("VCAP_SERVICES", "").replace("'", '"')
    vcap_services = json.loads(json_acceptable_string)

    database_credentials = {
        database_service["name"]: database_service["credentials"]["uri"]
        for database_service in vcap_services["postgres"]
        if database_service["name"] in DATABASE_SERVICE_NAMES
    }

    DATABASES["default"] = dj_database_url.parse(
        database_credentials["monitoring-platform-default-db"]
    )

    if "a11ymon-postgres" in database_credentials:
        DATABASES["pubsecweb_db"] = dj_database_url.parse(
            database_credentials["a11ymon-postgres"]
        )
        DATABASES["pubsecweb_db"]["OPTIONS"] = {  # type: ignore
            "options": "-c search_path=pubsecweb,public"
        }
        DATABASES["a11ymon_db"] = dj_database_url.parse(
            database_credentials["a11ymon-postgres"]
        )
        DATABASES["a11ymon_db"]["OPTIONS"] = {"options": "-c search_path=a11ymon,public"}  # type: ignore

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "dashboard:home"


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_DIRS = [BASE_DIR / "static/compiled/"]

STATIC_URL = os.path.join(BASE_DIR, "/static/")
STATIC_ROOT = os.path.join(BASE_DIR, "static/dist")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CONTACT_ADMIN_EMAIL = "accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
