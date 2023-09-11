"""
Django settings for report_viewer project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import sys
import os
import json
from dotenv import load_dotenv


DEBUG = os.getenv("DEBUG") == "TRUE"

UNDER_TEST = (len(sys.argv) > 1 and sys.argv[1] == "test") or "pytest" in sys.modules
INTEGRATION_TEST = os.getenv("INTEGRATION_TEST") == "TRUE"

S3_MOCK_ENDPOINT = None
if os.getenv("INTEGRATION_TEST") == "TRUE":
    S3_MOCK_ENDPOINT = "http://localstack:4566"
elif DEBUG and not UNDER_TEST:
    S3_MOCK_ENDPOINT = "http://localhost:4566"

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(" ")

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
CSRF_TRUSTED_ORIGINS.append("http://localhost:3000")  # BrowserSync needs this to work


INSTALLED_APPS = [
    "report_viewer.apps.viewer",
    "accessibility_monitoring_platform.apps.comments",
    "accessibility_monitoring_platform.apps.common",
    "accessibility_monitoring_platform.apps.cases",
    "accessibility_monitoring_platform.apps.s3_read_write",
    "accessibility_monitoring_platform.apps.reports",
    "accessibility_monitoring_platform.apps.audits",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",  # <- if you want email capability.
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "accessibility_monitoring_platform.apps.common.middleware.healthcheck_middleware.HealthcheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accessibility_monitoring_platform.apps.common.middleware.permissions_policy_middleware.PermissionsPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
    "report_viewer.apps.viewer.middleware.report_views_middleware.ReportMetrics",
]

ROOT_URLCONF = "report_viewer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR.parent, "common/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "accessibility_monitoring_platform.apps.common.templatetags.common_tags"
            ],
        },
    },
]

WSGI_APPLICATION = "report_viewer.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {}

if UNDER_TEST or INTEGRATION_TEST:
    if INTEGRATION_TEST:
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_NAME"),
            "USER": os.environ.get("POSTGRES_USER"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("POSTGRES_HOST"),
            "PORT": os.environ.get("POSTGRES_PORT"),
        }
    else:
        DATABASES["default"] = {
            "NAME": "accessibility_monitoring_app",
            "ENGINE": "django.db.backends.sqlite3",
        }
    DATABASES["aws-s3-bucket"] = {
        "aws_access_key_id": "key",
        "aws_region": "us-east-1",
        "aws_secret_access_key": "secret",
        "bucket_name": "bucketname",
        "deploy_env": "",
    }
elif os.getenv("DB_SECRET") and os.getenv("DB_NAME"):
    db_secrets: str = os.environ["DB_SECRET"]
    json_acceptable_string: str = db_secrets.replace("'", '"')
    db_secrets_dict = json.loads(json_acceptable_string)
    DATABASES["default"] = {
        "NAME": db_secrets_dict["dbname"],
        "USER": db_secrets_dict["username"],
        "PASSWORD": db_secrets_dict["password"],
        "HOST": db_secrets_dict["host"],
        "PORT": db_secrets_dict["port"],
        "CONN_MAX_AGE": 0,
        "ENGINE": "django.db.backends.postgresql",
    }
    bucket_name: str = os.environ["DB_NAME"]
    DATABASES["aws-s3-bucket"] = {
        "bucket_name": bucket_name,
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
        "aws_region": None,
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}
# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


# LOGIN_REDIRECT_URL = "homepage:home"
# LOGOUT_REDIRECT_URL = "dashboard:home"


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_DIRS = [f"{Path(BASE_DIR).parent}/common/static/compiled"]
STATIC_URL = os.path.join(BASE_DIR, "/static/")
STATIC_ROOT = os.path.join(BASE_DIR, "static/dist")

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
CONTACT_ADMIN_EMAIL = (
    "accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk"
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATE_FORMAT = "d/m/Y"

MARKDOWN_EXTENSIONS = []

PERMISSIONS_POLICY = {
    "accelerometer": [],
    # "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    # "interest-cohort": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}

CSP_DEFAULT_SRC = ("'none'",)
CSP_STYLE_SRC = "'self'"
CSP_SCRIPT_SRC = ("'self'",)
CSP_FONT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:")


aws_prototype_filename: str = "aws_prototype.json"
if os.path.isfile(aws_prototype_filename):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
