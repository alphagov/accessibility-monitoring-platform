"""
Admin - users
"""

from django.contrib import admin

# Register your models here.

from .models import EmailInclusionList

admin.site.register(EmailInclusionList)
