"""Django admin configuration for websites app"""
from django.contrib import admin

from .models import Website


class WebsiteAdmin(admin.ModelAdmin):
    """Django admin configuration for Website model"""

    list_display = ["url", "response_status_code", "response_type"]
    list_filter = ["response_type", "response_status_code"]
    readonly_fields = ["url", "response_status_code", "response_headers", "response_content"]
    search_fields = ["url", "response_status_code", "response_headers", "response_content"]


admin.site.register(Website, WebsiteAdmin)
