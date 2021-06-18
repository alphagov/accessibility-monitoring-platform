"""
Admin - users
"""

from django.contrib import admin

from .models import EmailInclusionList

admin.site.register(EmailInclusionList)
