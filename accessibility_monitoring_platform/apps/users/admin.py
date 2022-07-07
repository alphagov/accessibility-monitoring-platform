"""
Admin - users
"""

from django.contrib import admin

from .models import AllowedEmail

admin.site.register(AllowedEmail)
