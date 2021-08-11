"""
Admin for common app
"""
from django.contrib import admin

from .models import IssueReport, Sector


class IssueReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["page_url", "page_title", "description", "created", "created_by"]
    search_fields = ["page_url", "page_title", "description"]
    list_display = ["page_title", "created_by", "created", "description"]
    list_filter = ["created_by"]


admin.site.register(IssueReport, IssueReportAdmin)
admin.site.register(Sector)
