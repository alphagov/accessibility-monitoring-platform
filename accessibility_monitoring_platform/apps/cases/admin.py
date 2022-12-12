"""
Admin for cases
"""
from django.contrib import admin

from .models import Case, CaseEvent, Contact


class CaseAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["created"]
    search_fields = ["organisation_name", "domain"]
    list_display = ["organisation_name", "domain", "auditor", "created"]
    list_filter = ["auditor"]


class CaseEventAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseEvent model"""

    readonly_fields = ["case", "type", "message", "created", "created_by"]
    search_fields = ["case__organisation_name", "case__id"]
    list_display = ["case", "created", "type", "created_by", "message"]
    list_filter = ["type"]


class ContactAdmin(admin.ModelAdmin):
    """Django admin configuration for Contact model"""

    search_fields = [
        "name",
        "job_title",
        "email",
        "case__organisation_name",
    ]
    list_display = ["email", "name", "job_title", "case"]
    autocomplete_fields = ["case"]


admin.site.register(Case, CaseAdmin)
admin.site.register(CaseEvent, CaseEventAdmin)
admin.site.register(Contact, ContactAdmin)
