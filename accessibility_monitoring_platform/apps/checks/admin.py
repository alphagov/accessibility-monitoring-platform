"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from .models import Check, Page, CheckTest, WcagTest


class WcagTestAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagTest model"""

    search_fields = ["name"]
    list_display = ["id", "type", "sub_type", "name"]
    list_filter = ["type", "sub_type"]


admin.site.register(Check)
admin.site.register(Page)
admin.site.register(CheckTest)
admin.site.register(WcagTest, WcagTestAdmin)
