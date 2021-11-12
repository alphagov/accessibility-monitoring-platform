"""
Admin for reminders
"""

from django.contrib import admin

from .models import Reminder


class ReminderAdmin(admin.ModelAdmin):
    """Django admin configuration for Reminder model"""

    search_fields = ["case", "description"]
    list_display = ["case", "due_date", "is_deleted", "description"]
    list_filter = ["is_deleted"]


admin.site.register(Reminder, ReminderAdmin)
