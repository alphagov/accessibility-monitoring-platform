"""
Admin for common app
"""
import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import IssueReport, Sector


class IssueReportAdmin(admin.ModelAdmin):
    """Django admin configuration for Case model"""

    readonly_fields = ["page_url", "page_title", "description", "created", "created_by"]
    search_fields = ["page_url", "page_title", "description"]
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

    @admin.action(description="Export selected issues as csv")
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response


admin.site.register(IssueReport, IssueReportAdmin)
admin.site.register(Sector)
