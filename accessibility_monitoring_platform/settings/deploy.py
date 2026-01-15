"""
Production deployment settings
"""

import os
from pathlib import Path

from .base import *

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

AWS_PROTOTYPE_FILE: Path = Path("aws_prototype.json")
if AWS_PROTOTYPE_FILE.exists():
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
elif os.getenv("NOTIFY_API_KEY"):
    EMAIL_BACKEND: str = "accessibility_monitoring_platform.email.NotifyEmailBackend"
    EMAIL_NOTIFY_API_KEY = os.getenv("NOTIFY_API_KEY")
    EMAIL_NOTIFY_BASIC_TEMPLATE = os.getenv("EMAIL_NOTIFY_BASIC_TEMPLATE")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_HSTS_SECONDS = 2592000  # One month in seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_AGE = 60 * 60 * 24 * 6  # Six days in seconds
