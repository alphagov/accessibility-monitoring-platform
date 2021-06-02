"""
Admin for cases
"""
from django.contrib import admin

from .models import Case, Contact


class CaseAdmin(admin.ModelAdmin):
    readonly_fields = ["simplified_test_filename", "created"]
    search_fields = ["organisation_name"]
    list_display = ["organisation_name", "domain", "auditor", "created"]
    list_filter = ["auditor"]


class ContactAdmin(admin.ModelAdmin):
    search_fields = ["name", "job_title", "detail", "case__organisation_name"]
    list_display = ["name", "job_title", "detail", "case"]
    autocomplete_fields = ["case"]

admin.site.register(Case, CaseAdmin)
admin.site.register(Contact, ContactAdmin)
