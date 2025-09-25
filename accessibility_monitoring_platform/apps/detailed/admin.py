"""
Admin for cases
"""

from django.contrib import admin

from .models import (
    Contact,
    DetailedCase,
    DetailedCaseHistory,
    DetailedEventHistory,
    ZendeskTicket,
)


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
        "status",
    ]
    show_facets = admin.ShowFacets.ALWAYS


class DetailedCaseHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for DetailedCaseHistory model"""

    readonly_fields = ["detailed_case", "event_type", "created_by", "created"]
    search_fields = [
        "detailed_case__case_number",
        "detailed_case__organisation_name",
        "label",
        "value",
    ]
    list_display = [
        "detailed_case",
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


class DetailedEventHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for DetailedEventHistory model"""

    search_fields = [
        "detailed_case__organisation_name",
        "detailed_case__case_number",
    ]
    list_display = [
        "detailed_case",
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
    readonly_fields = ["detailed_case"]
    show_facets = admin.ShowFacets.ALWAYS


class ContactAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "contact_details",
        "detailed_case__organisation_name",
        "detailed_case__case_number",
    ]
    list_display = [
        "__str__",
        "name",
        "contact_details",
        "detailed_case",
        "is_deleted",
    ]
    list_filter = ["is_deleted"]
    show_facets = admin.ShowFacets.ALWAYS


class ZendeskTicketAdmin(admin.ModelAdmin):
    """Django admin configuration for ZendeskTicket model"""

    search_fields = [
        "url",
        "summary",
        "detailed_case__organisation_name",
        "detailed_case__case_number",
    ]
    list_display = ["url", "summary", "detailed_case", "created", "is_deleted"]
    list_filter = ["is_deleted"]


admin.site.register(DetailedCase, DetailedCaseAdmin)
admin.site.register(DetailedCaseHistory, DetailedCaseHistoryAdmin)
admin.site.register(DetailedEventHistory, DetailedEventHistoryAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(ZendeskTicket, ZendeskTicketAdmin)
