"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from .models import Check, Page

admin.site.register(Check)
admin.site.register(Page)
