"""
Admin for cases
"""
from django.contrib import admin

from .models import Case, Contact, CLOSED_CASE_STATUSES


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
            return queryset.exclude(status__in=CLOSED_CASE_STATUSES)
        return queryset.filter(status__in=CLOSED_CASE_STATUSES)


class HistoricAuditorCaseListFilter(admin.SimpleListFilter):
    """Filter by list of statuses which mean Case is closed"""

    title = "Historic auditors"

    parameter_name = "historic_auditor"

    def lookups(self, request, model_admin):
        """Return list of values and labels for filter"""
        return (
            ("open", "Open"),
            ("closed", "Closed"),
        )

    def queryset(self, request, queryset):
        """Returns queryset with filter applied"""
        if self.value() == "open":
            return queryset.exclude(status__in=CLOSED_CASE_STATUSES)
        return queryset.filter(status__in=CLOSED_CASE_STATUSES)


class CaseAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["created"]
    search_fields = ["organisation_name", "domain"]
    list_display = ["organisation_name", "domain", "auditor", "created", "status"]
    list_filter = [
        MetaStatusCaseListFilter,
        "testing_methodology",
        "report_methodology",
        ("auditor", admin.RelatedOnlyFieldListFilter),
    ]


class ContactAdmin(admin.ModelAdmin):
    """Django admin configuration for Contact model"""

    search_fields = [
        "name",
        "job_title",
        "email",
        "case__organisation_name",
    ]
    list_display = ["email", "name", "job_title", "case"]
    autocomplete_fields = ["case"]


admin.site.register(Case, CaseAdmin)
admin.site.register(Contact, ContactAdmin)
