"""
Admin for S3 read write
"""

from django.contrib import admin

from .models import S3Report


class S3ReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Section model"""

    readonly_fields = ["created", "version"]
    search_fields = ["guid", "base_case__organisation_name", "created_by__email"]
    list_display = ["__str__", "base_case", "created_by", "created", "latest_published"]
    list_filter = ["latest_published"]


admin.site.register(S3Report, S3ReportAdmin)
