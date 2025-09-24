"""
Admin for cases
"""

from django.contrib import admin

from .models import BaseCase


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


admin.site.register(BaseCase, BaseCaseAdmin)
