"""
Admin for cases
"""
from django.contrib import admin

from .models import Case, Contact


class CaseAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["simplified_test_filename", "created"]
    search_fields = ["organisation_name"]
    list_display = ["organisation_name", "domain", "auditor", "created"]
    list_filter = ["auditor"]
    filter_horizontal = ["region"]


class ContactAdmin(admin.ModelAdmin):
    """Django admin configuration for Contact model"""

    search_fields = [
        "first_name",
        "last_name",
        "job_title",
        "detail",
        "case__organisation_name",
    ]
    list_display = ["detail", "first_name", "last_name", "job_title", "case"]
    autocomplete_fields = ["case"]


admin.site.register(Case, CaseAdmin)
admin.site.register(Contact, ContactAdmin)
