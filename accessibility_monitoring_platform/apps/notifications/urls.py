"""
URLS for notifications
"""

from django.contrib.auth.decorators import login_required
from django.urls import path

from accessibility_monitoring_platform.apps.notifications.views import (
    ReminderTaskUpdateView,
    TaskListView,
    TaskMarkAsReadView,
)

app_name = "notifications"
urlpatterns = [
    path(
        "task-list/",
        login_required(TaskListView.as_view()),
        name="task-list",
    ),
    path(
        "<int:pk>/edit-reminder-task/",
        login_required(ReminderTaskUpdateView.as_view()),
        name="edit-reminder-task",
    ),
    path(
        "<int:pk>/mark-task-read/",
        login_required(TaskMarkAsReadView.as_view()),
        name="mark-task-read",
    ),
]
