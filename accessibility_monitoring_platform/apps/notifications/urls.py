"""
URLS for notifications
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from accessibility_monitoring_platform.apps.notifications.views import (
    NotificationView,
    NotificationMarkAsReadView,
    NotificationMarkAsUnreadView,
)


app_name = "notifications"
urlpatterns = [
    path(
        "notifications-list/",
        login_required(NotificationView.as_view()),
        name="notifications-list",
    ),
    path(
        "<int:pk>/mark-notification-read/",
        login_required(NotificationMarkAsReadView.as_view()),
        name="mark-notification-read",
    ),
    path(
        "<int:pk>/mark-notification-unread/",
        login_required(NotificationMarkAsUnreadView.as_view()),
        name="mark-notification-unread",
    ),
]
