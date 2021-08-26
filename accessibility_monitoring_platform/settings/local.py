"""
Local deployment settings
"""

from .base import *

AUTH_PASSWORD_VALIDATORS = []
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
