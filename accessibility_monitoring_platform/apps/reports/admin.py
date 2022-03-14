"""
Admin for reports
"""
from django.contrib import admin

from .models import Report


class ReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Report model"""

    readonly_fields = ["created"]
    search_fields = ["case__organisation_name"]
    list_display = ["case", "created"]
    list_filter = ["ready_for_qa"]


admin.site.register(Report, ReportAdmin)
