"""
Admin for common app
"""
from django.contrib import admin

from .models import Sector

admin.site.register(Sector)
