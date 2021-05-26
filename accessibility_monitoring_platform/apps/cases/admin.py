"""
Admin for cases
"""
from django.contrib import admin

from .models import Case


class CaseAdmin(admin.ModelAdmin):
    readonly_fields = ["simplified_test_filename", "created"]
    search_fields = ["website_name"]
    list_display = ["website_name", "auditor", "created"]
    list_filter = ["auditor"]
    fieldsets = (
        (None, {
            "fields": (
                "website_name",
                "home_page_url",
                "auditor",
                "simplified_test_filename",
                "created",
                "created_by",
                )
            }
        ),
    )

admin.site.register(Case, CaseAdmin)
