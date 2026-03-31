"""
Admin for cases
"""

from django.contrib import admin

from .models import BaseCase, CaseFile


class BaseCaseAdmin(admin.ModelAdmin):
    """Django admin configuration for BaseCase model"""

    readonly_fields = ["created"]
    search_fields = ["case_number", "organisation_name", "domain"]
    list_display = [
        "case_number",
        "organisation_name",
        "domain",
        "auditor",
        "created",
        "status",
    ]
    list_filter = [
        "status",
        ("auditor", admin.RelatedOnlyFieldListFilter),
        ("reviewer", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


class CaseFileAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseFile model"""

    readonly_fields = ["uploaded_time"]
    search_fields = ["base_case__case_number", "base_case__organisation_name", "name"]
    list_display = [
        "name",
        "type",
        "base_case",
        "uploaded_time",
        "uploaded_by",
        "is_deleted",
    ]
    list_filter = [
        "type",
        "is_deleted",
        ("uploaded_by", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(BaseCase, BaseCaseAdmin)
admin.site.register(CaseFile, CaseFileAdmin)
