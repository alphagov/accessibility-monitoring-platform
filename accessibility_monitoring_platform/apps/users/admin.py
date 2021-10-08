"""
Admin - users
"""

from django.contrib import admin

from .models import Auditor, EmailInclusionList

admin.site.register(Auditor)
admin.site.register(EmailInclusionList)
