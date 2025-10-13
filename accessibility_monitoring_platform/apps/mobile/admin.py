"""
Admin for cases
"""

from django.contrib import admin

from .models import EventHistory, MobileCase


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


class EventHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for mobile EventHistory model"""

    search_fields = [
        "mobile_case__organisation_name",
        "mobile_case__case_number",
    ]
    list_display = [
        "mobile_case",
        "event_type",
        "content_type",
        "created",
        "created_by",
        "difference",
    ]
    list_filter = [
        "event_type",
        ("content_type", admin.RelatedOnlyFieldListFilter),
        ("created_by", admin.RelatedOnlyFieldListFilter),
    ]
    readonly_fields = ["mobile_case"]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(MobileCase, MobileCaseAdmin)
admin.site.register(EventHistory, EventHistoryAdmin)
