"""
Admin for cases
"""
from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import (
    Case,
    CaseCompliance,
    CaseStatus,
    CaseEvent,
    Contact,
    EqualityBodyCorrespondence,
    CLOSED_CASE_STATUSES,
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
            return queryset.exclude(status__status__in=CLOSED_CASE_STATUSES)
        if self.value() == "closed":
            return queryset.filter(status__status__in=CLOSED_CASE_STATUSES)


class CaseAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["created"]
    search_fields = ["organisation_name", "domain"]
    list_display = ["organisation_name", "domain", "auditor", "created", "status"]
    list_filter = [
        MetaStatusCaseListFilter,
        ("auditor", admin.RelatedOnlyFieldListFilter),
    ]


class CaseStatusAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseStatus model"""

    readonly_fields = ["case"]
    search_fields = ["case__organisation_name", "case__id"]
    list_filter = ["status"]


class CaseComplianceAdmin(admin.ModelAdmin):
    """Django admin configuration for CaseCompliance model"""

    readonly_fields = ["case"]
    search_fields = ["case__organisation_name", "case__id"]
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


class CaseEventAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for CaseEvent model"""

    readonly_fields = ["case", "event_type", "message", "event_time", "done_by"]
    search_fields = [
        "case__organisation_name",
        "case__id",
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
        "case__id",
    ]
    list_display = ["email", "name", "job_title", "case"]
    autocomplete_fields = ["case"]


class EqualityBodyCorrespondenceAdmin(admin.ModelAdmin):
    """Django admin configuration for EqualityBodyCorrespondence model"""

    search_fields = [
        "message",
        "notes",
        "case__organisation_name",
        "case__id",
    ]
    list_display = ["created", "case", "type", "status", "message"]
    list_filter = ["type", "status"]


admin.site.register(Case, CaseAdmin)
admin.site.register(CaseStatus, CaseStatusAdmin)
admin.site.register(CaseCompliance, CaseComplianceAdmin)
admin.site.register(CaseEvent, CaseEventAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(EqualityBodyCorrespondence, EqualityBodyCorrespondenceAdmin)
