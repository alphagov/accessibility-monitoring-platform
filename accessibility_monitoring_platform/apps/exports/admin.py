"""Admin - admin page for comments"""

from django.contrib import admin

from .models import Export, ExportCase


class ExportAdmin(admin.ModelAdmin):
    """Django admin configuration for Export model"""

    readonly_fields = ["created"]
    search_fields = [
        "exporter__username",
    ]
    list_display = [
        "cutoff_date",
        "exporter",
        "status",
        "enforcement_body",
    ]
    list_filter = ["status"]
    show_facets = admin.ShowFacets.ALWAYS


class ExportCaseAdmin(admin.ModelAdmin):
    """Django admin configuration for ExportCase model"""

    search_fields = [
        "export__exporter__username",
        "case__organisation_name",
        "case__id",
    ]
    list_display = [
        "export",
        "case",
        "status",
    ]
    list_filter = ["status"]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Export, ExportAdmin)
admin.site.register(ExportCase, ExportCaseAdmin)
