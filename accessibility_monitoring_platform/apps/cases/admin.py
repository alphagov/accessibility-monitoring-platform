"""
Admin for cases
"""

from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import (
    Case,
    CaseCompliance,
    CaseEvent,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
    ZendeskTicket,
)


class MetaStatusCaseListFilter(admin.SimpleListFilter):
    """Filter by list of statuses which mean Case is closed"""

    title = "Meta statuses"

    parameter_name = "meta_status"

    def lookups(self, request, model_admin):
        """Return list of values and labels for filter"""
        return (
            ("open", "Open"),
            ("closed", "Closed"),
        )

    def queryset(self, request, queryset):
        """Returns queryset with filter applied"""
        if self.value() == "open":
            return queryset.exclude(status__status__in=CaseStatus.CLOSED_CASE_STATUSES)
        if self.value() == "closed":
            return queryset.filter(status__status__in=CaseStatus.CLOSED_CASE_STATUSES)


class CaseAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

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
        "variant",
        MetaStatusCaseListFilter,
        ("auditor", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


class CaseStatusAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseStatus model"""

    readonly_fields = ["case"]
    search_fields = ["case__organisation_name", "case__case_number"]
    list_filter = ["status"]
    show_facets = admin.ShowFacets.ALWAYS


class CaseComplianceAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseCompliance model"""

    readonly_fields = ["case"]
    search_fields = ["case__organisation_name", "case__case_number"]
    list_display = [
        "case",
        "__str__",
    ]
    list_filter = [
        "website_compliance_state_initial",
        "website_compliance_state_12_week",
        "statement_compliance_state_initial",
        "statement_compliance_state_12_week",
    ]
    show_facets = admin.ShowFacets.ALWAYS


class CaseEventAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for CaseEvent model"""

    readonly_fields = ["case", "event_type", "message", "event_time", "done_by"]
    search_fields = [
        "case__organisation_name",
        "case__case_number",
        "message",
        "done_by__username",
    ]
    list_display = ["message", "event_time", "done_by", "case", "event_type"]
    list_filter = ["event_type", ("done_by", admin.RelatedOnlyFieldListFilter)]
    actions = ["export_as_csv"]


class ContactAdmin(admin.ModelAdmin):
    """Django admin configuration for Contact model"""

    search_fields = [
        "name",
        "job_title",
        "email",
        "case__organisation_name",
        "case__case_number",
    ]
    list_display = ["email", "name", "job_title", "case"]
    autocomplete_fields = ["case"]


class EqualityBodyCorrespondenceAdmin(admin.ModelAdmin):
    """Django admin configuration for EqualityBodyCorrespondence model"""

    search_fields = [
        "message",
        "notes",
        "case__organisation_name",
        "case__case_number",
    ]
    list_display = ["created", "case", "type", "status", "message"]
    list_filter = ["type", "status"]


class ZendeskTicketAdmin(admin.ModelAdmin):
    """Django admin configuration for EqualityBodyCorrespondence model"""

    search_fields = [
        "url",
        "summary",
        "case__organisation_name",
        "case__case_number",
    ]
    list_display = ["url", "summary", "case", "created", "is_deleted"]
    list_filter = ["is_deleted"]


admin.site.register(Case, CaseAdmin)
admin.site.register(CaseStatus, CaseStatusAdmin)
admin.site.register(CaseCompliance, CaseComplianceAdmin)
admin.site.register(CaseEvent, CaseEventAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(EqualityBodyCorrespondence, EqualityBodyCorrespondenceAdmin)
admin.site.register(ZendeskTicket, ZendeskTicketAdmin)
