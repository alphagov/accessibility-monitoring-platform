"""
Django settings for accessibility_monitoring_platform project.

Generated by 'django-admin startproject' using Django 3.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

DEBUG = os.getenv("DEBUG") == "TRUE"

UNDER_TEST = (len(sys.argv) > 1 and sys.argv[1] == "test") or "pytest" in sys.modules
INTEGRATION_TEST = os.getenv("INTEGRATION_TEST") == "TRUE"

S3_MOCK_ENDPOINT = None
if INTEGRATION_TEST:
    S3_MOCK_ENDPOINT = "http://localstack:4566"
elif DEBUG and not UNDER_TEST:
    S3_MOCK_ENDPOINT = "http://localhost:4566"

load_dotenv()

CURRENT_FILE: Path = Path(__file__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR: Path = CURRENT_FILE.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(" ")

CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
CSRF_TRUSTED_ORIGINS.append("http://localhost:3000")

# Application definition

INSTALLED_APPS = [
    "accessibility_monitoring_platform.apps.cases",
    "accessibility_monitoring_platform.apps.audits",
    "accessibility_monitoring_platform.apps.common",
    "accessibility_monitoring_platform.apps.dashboard",
    "accessibility_monitoring_platform.apps.users",
    "accessibility_monitoring_platform.apps.notifications",
    "accessibility_monitoring_platform.apps.exports",
    "accessibility_monitoring_platform.apps.comments",
    "accessibility_monitoring_platform.apps.reports",
    "accessibility_monitoring_platform.apps.s3_read_write",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "axes",
    "django_browser_reload",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",  # <- if you want email capability.
    "two_factor",
    "two_factor.plugins.email",  # <- if you want email capability.
]

AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    "accessibility_monitoring_platform.apps.common.middleware.healthcheck_middleware.HealthcheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "accessibility_monitoring_platform.apps.common.middleware.permissions_policy_middleware.PermissionsPolicyMiddleware",
    "accessibility_monitoring_platform.apps.common.middleware.cache_user_id_middleware.CacheUserUniqueID",
    "csp.middleware.CSPMiddleware",
    # AxesMiddleware should be the last middleware in the MIDDLEWARE list.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "accessibility_monitoring_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR.parent / "common" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accessibility_monitoring_platform.apps.common.context_processors.platform_page",
            ],
            "builtins": [
                "accessibility_monitoring_platform.apps.common.templatetags.common_tags"
            ],
        },
    },
]


DATABASES = {}

if UNDER_TEST or INTEGRATION_TEST:
    if INTEGRATION_TEST:
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_NAME"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ["POSTGRES_PORT"],
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


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
            "level": "INFO",
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/


LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "dashboard:home"
LOGIN_URL = "two_factor:login"


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_DIRS = [BASE_DIR.parent / "common" / "static" / "compiled"]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static" / "dist"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CONTACT_ADMIN_EMAIL = (
    "accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk"
)

DEFAULT_FROM_EMAIL = (
    "accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk"
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DATE_FORMAT = "d/m/Y"

MARKDOWN_EXTENSIONS = ["fenced_code", "sane_lists"]

# django-axes
AXES_LOCKOUT_PARAMETERS = ["username"]  # Block only on username
AXES_FAILURE_LIMIT = 20

if UNDER_TEST:
    #  django-axes is incompatible with the platform test environment
    INSTALLED_APPS.remove("axes")
    AUTHENTICATION_BACKENDS.remove("axes.backends.AxesBackend")
    MIDDLEWARE.remove("axes.middleware.AxesMiddleware")


TWO_FACTOR_REMEMBER_COOKIE_AGE = 60 * 60 * 24 * 6  # 2FA expires after 6 days

PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "interest-cohort": [],
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

AWS_PROTOTYPE_FILE: Path = Path("aws_prototype.json")
if AWS_PROTOTYPE_FILE.exists() and UNDER_TEST is False:
    aws_prototype_text: str = AWS_PROTOTYPE_FILE.read_text()
    aws_prototype_data: dict = json.loads(aws_prototype_text)
    AMP_PROTOTYPE_NAME = aws_prototype_data["prototype_name"]
    AMP_PROTOCOL: str = aws_prototype_data["amp_protocol"]
    AMP_VIEWER_DOMAIN: str = aws_prototype_data["viewer_domain"]
else:
    AMP_PROTOTYPE_NAME = os.getenv("AMP_PROTOTYPE_NAME", "")
    AMP_PROTOCOL = os.getenv("AMP_PROTOCOL", "http://")
    AMP_VIEWER_DOMAIN = os.getenv("AMP_VIEWER_DOMAIN", "localhost:8002")

COPILOT_APPLICATION_NAME = os.getenv("COPILOT_APPLICATION_NAME", None)

OTP_EMAIL_SUBJECT = "Platform token"
