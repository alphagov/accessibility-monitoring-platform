"""
Production deployment settings
"""

import os
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

EMAIL_BACKEND = "accessibility_monitoring_platform.email.NotifyEmailBackend"
EMAIL_NOTIFY_API_KEY = os.getenv("EMAIL_NOTIFY_API_KEY")
EMAIL_NOTIFY_BASIC_TEMPLATE = os.getenv("EMAIL_NOTIFY_BASIC_TEMPLATE")
