"""
Admin for reminders
"""
from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import Reminder


class ReminderAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for Reminder model"""

    search_fields = ["case__organisation_name", "description"]
    list_display = ["case", "due_date", "is_deleted", "description"]
    list_filter = ["is_deleted", ("case__auditor", admin.RelatedOnlyFieldListFilter)]
    actions = ["export_as_csv"]


admin.site.register(Reminder, ReminderAdmin)
