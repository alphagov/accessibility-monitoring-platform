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
        "is_deleted",
    ]
    list_filter = ["status", "is_deleted"]
    show_facets = admin.ShowFacets.ALWAYS


class ExportCaseAdmin(admin.ModelAdmin):
    """Django admin configuration for ExportCase model"""

    search_fields = [
        "export__exporter__username",
        "simplified_case__organisation_name",
        "simplified_case__case_number",
    ]
    list_display = [
        "export",
        "simplified_case",
        "status",
    ]
    list_filter = ["status"]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Export, ExportAdmin)
admin.site.register(ExportCase, ExportCaseAdmin)
