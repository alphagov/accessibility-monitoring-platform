"""
Admin for common app
"""
import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import (
    Event,
    IssueReport,
    Platform,
    ChangeToPlatform,
    Sector,
    UserCacheUniqueHash,
    FrequentlyUsedLink,
    FooterLink,
)


class ExportCsvMixin:
    """Mixin which adds csv export django admin action"""

    def export_as_csv(self, request, queryset):  # pylint: disable=unused-argument
        meta = self.model._meta  # pylint: disable=protected-access
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


class EventAdmin(admin.ModelAdmin):
    """Django admin configuration for Event model"""

    readonly_fields = [
        "content_type",
        "object_id",
        "value",
        "created",
        "created_by",
        "old_fields",
        "new_fields",
        "diff",
    ]
    search_fields = ["value", "created_by__username"]
    list_display = [
        "content_type",
        "object_id",
        "type",
        "created",
        "created_by",
        "diff",
    ]
    list_filter = ["type", ("content_type", admin.RelatedOnlyFieldListFilter)]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("content_type", "object_id"),
                    ("created_by", "created"),
                    ("diff",),
                    ("old_fields",),
                    ("new_fields",),
                    ("value",),
                )
            },
        ),
    )


class IssueReportAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for IssueReport model"""

    readonly_fields = ["page_url", "page_title", "description", "created", "created_by"]
    search_fields = ["page_url", "page_title", "description", "trello_ticket"]
    list_display = ["page_title", "created_by", "created", "complete", "description"]
    list_filter = ["complete", "created_by"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("page_title", "page_url"),
                    ("created_by", "created"),
                    ("description",),
                    ("trello_ticket", "complete"),
                    ("notes",),
                )
            },
        ),
    )

    actions = ["export_as_csv"]

    def has_delete_permission(
        self, request, obj=None
    ):  # pylint: disable=unused-argument
        return False


class ChangeToPlatformAdmin(admin.ModelAdmin):
    """Django admin configuration for ChangeToPlatform model"""

    search_fields = ["name", "notes"]
    list_display = ["name", "created"]
    date_hierarchy = "created"


class UserCacheUniqueHashAdmin(admin.ModelAdmin):
    """Django admin configuration for IssueReport model"""

    readonly_fields = ["user", "fingerprint_hash"]
    search_fields = ["user"]
    list_display = ["user", "fingerprint_hash"]
    list_filter = ["user", "fingerprint_hash"]


class FrequentlyUsedLinksAdmin(admin.ModelAdmin):
    """ "Django admin configuration for FrequentlyUsedLink model"""

    list_display = ["label", "url", "is_deleted"]


class FooterLinksAdmin(admin.ModelAdmin):
    """ "Django admin configuration for FooterLink model"""

    list_display = ["label", "url", "is_deleted"]


admin.site.register(Event, EventAdmin)
admin.site.register(IssueReport, IssueReportAdmin)
admin.site.register(Platform)
admin.site.register(ChangeToPlatform, ChangeToPlatformAdmin)
admin.site.register(Sector)
admin.site.register(UserCacheUniqueHash, UserCacheUniqueHashAdmin)
admin.site.register(FrequentlyUsedLink, FrequentlyUsedLinksAdmin)
admin.site.register(FooterLink, FooterLinksAdmin)
