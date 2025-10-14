"""
Admin for cases
"""

from django.contrib import admin

from .models import (
    EventHistory,
    MobileCase,
    MobileCaseHistory,
    MobileContact,
    MobileZendeskTicket,
)


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


class MobileCaseHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for MobileCaseHistory model"""

    readonly_fields = ["mobile_case", "event_type", "created_by", "created"]
    search_fields = [
        "mobile_case__case_number",
        "mobile_case__organisation_name",
        "label",
        "value",
    ]
    list_display = [
        "mobile_case",
        "event_type",
        "label",
        "created_by",
        "created",
    ]
    list_filter = [
        "event_type",
        ("created_by", admin.RelatedOnlyFieldListFilter),
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


class ContactAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "contact_details",
        "mobile_case__organisation_name",
        "mobile_case__case_number",
    ]
    list_display = [
        "__str__",
        "name",
        "contact_details",
        "mobile_case",
        "is_deleted",
    ]
    list_filter = ["is_deleted"]
    show_facets = admin.ShowFacets.ALWAYS


class ZendeskTicketAdmin(admin.ModelAdmin):
    """Django admin configuration for ZendeskTicket model"""

    search_fields = [
        "url",
        "summary",
        "mobile_case__organisation_name",
        "mobile_case__case_number",
    ]
    list_display = ["url", "summary", "mobile_case", "created", "is_deleted"]
    list_filter = ["is_deleted"]


admin.site.register(MobileCase, MobileCaseAdmin)
admin.site.register(MobileCaseHistory, MobileCaseHistoryAdmin)
admin.site.register(EventHistory, EventHistoryAdmin)
admin.site.register(MobileContact, ContactAdmin)
admin.site.register(MobileZendeskTicket, ZendeskTicketAdmin)
