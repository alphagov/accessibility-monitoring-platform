"""
Admin for cases
"""
from django.contrib import admin

from .models import Case


class CaseAdmin(admin.ModelAdmin):
    readonly_fields = ["simplified_test_filename", "created"]
    search_fields = ["organisation_name"]
    list_display = ["organisation_name", "domain", "auditor", "created"]
    list_filter = ["auditor"]

admin.site.register(Case, CaseAdmin)
