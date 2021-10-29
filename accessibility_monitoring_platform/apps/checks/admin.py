"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from .models import Check, Page, CheckTest, WcagTest

admin.site.register(Check)
admin.site.register(Page)
admin.site.register(CheckTest)
admin.site.register(WcagTest)
