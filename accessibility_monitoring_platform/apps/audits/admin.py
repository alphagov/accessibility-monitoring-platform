"""
Admin for checks (called tests by the users)
"""

from django.contrib import admin

from .models import Audit, Page, PageTest, WcagDefinition


class WcagDefinitionAdmin(admin.ModelAdmin):
    """Django admin configuration for WcagDefinition model"""

    search_fields = ["name"]
    list_display = ["id", "type", "sub_type", "name"]
    list_filter = ["type", "sub_type"]


admin.site.register(Audit)
admin.site.register(Page)
admin.site.register(PageTest)
admin.site.register(WcagDefinition, WcagDefinitionAdmin)
