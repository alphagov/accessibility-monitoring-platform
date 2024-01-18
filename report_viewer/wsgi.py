"""
WSGI config for report_viewer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "report_viewer.settings.deploy",
)
# important that the whitenoise import is after the line above

application = get_wsgi_application()
application = WhiteNoise(application)
