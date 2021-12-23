"""
Admin for reminders
"""
from django.contrib import admin

from ..common.admin import ExportCsvMixin
from .models import Reminder


class ReminderAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Django admin configuration for Reminder model"""

    search_fields = ["case", "description"]
    list_display = ["case", "due_date", "is_deleted", "description"]
    list_filter = ["is_deleted"]
    actions = ["export_as_csv"]


admin.site.register(Reminder, ReminderAdmin)
