"""
Admin for cases
"""

from django.contrib import admin

from .models import Contact, DetailedCase, DetailedCaseHistory


class ContactAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "contact_point",
        "detailed_case__organisation_name",
        "detailed_case__case_number",
    ]
    list_display = [
        "__str__",
        "name",
        "contact_point",
        "detailed_case",
        "is_deleted",
    ]
    list_filter = ["is_deleted"]
    show_facets = admin.ShowFacets.ALWAYS


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


class DetailedCaseHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for DetailedCaseHistory model"""

    readonly_fields = ["detailed_case", "event_type", "created_by", "created"]
    search_fields = [
        "detailed_case__case_number",
        "detailed_case__organisation_name",
        "value",
    ]
    list_display = [
        "detailed_case",
        "event_type",
        "created_by",
        "created",
    ]
    list_filter = [
        "event_type",
        ("created_by", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Contact, ContactAdmin)
admin.site.register(DetailedCase, DetailedCaseAdmin)
admin.site.register(DetailedCaseHistory, DetailedCaseHistoryAdmin)
