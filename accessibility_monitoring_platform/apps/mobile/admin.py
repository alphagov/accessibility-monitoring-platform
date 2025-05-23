"""
Admin for cases
"""

from django.contrib import admin

from .models import MobileCase


class MobileCaseAdmin(admin.ModelAdmin):
    """Django admin configuration for MobileCase model"""

    readonly_fields = ["created"]
    search_fields = ["case_number", "organisation_name", "domain"]
    list_display = [
        "case_number",
        "organisation_name",
        "app_name",
        "auditor",
        "created",
    ]
    list_filter = [
        ("auditor", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(MobileCase, MobileCaseAdmin)
