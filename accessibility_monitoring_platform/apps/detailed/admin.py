"""
Admin for cases
"""

from django.contrib import admin

from .models import DetailedCase


class DetailedCaseAdmin(admin.ModelAdmin):
    """Django admin configuration for DetailedCase model"""

    readonly_fields = ["created"]
    search_fields = ["case_number", "organisation_name", "domain"]
    list_display = [
        "case_number",
        "organisation_name",
        "domain",
        "auditor",
        "created",
    ]
    list_filter = [
        ("auditor", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(DetailedCase, DetailedCaseAdmin)
