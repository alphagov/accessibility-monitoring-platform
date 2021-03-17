"""
WSGI config for notesapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
from whitenoise import WhiteNoise
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accessibility_monitoring_platform.settings")
# important that the whitenoise import is after the line above

application = get_wsgi_application()
application = WhiteNoise(application)
