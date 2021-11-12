"""
URLS for notifications
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    ReminderCreateView,
    ReminderListView,
    ReminderUpdateView,
    delete_reminder,
)


app_name = "reminders"
urlpatterns = [
    path(
        "cases/<int:case_id>/reminder-create/",
        login_required(ReminderCreateView.as_view()),
        name="reminder-create"
    ),
    path(
        "<int:pk>/edit-reminder/",
        login_required(ReminderUpdateView.as_view()),
        name="edit-reminder"
    ),
    path(
        "reminder-list/",
        login_required(ReminderListView.as_view()),
        name="reminder-list"
    ),
    path(
        "<int:pk>/delete-reminder/",
        login_required(delete_reminder),
        name="delete-reminder"
    ),
]
