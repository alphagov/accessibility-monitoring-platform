"""
URLS for notifications
"""

from django.urls import path
from django.contrib.auth.decorators import login_required
from accessibility_monitoring_platform.apps.notifications.views import NotificationsView, HideNotificationView


app_name = "notifications"
urlpatterns = [
    path(
        "notifications-list/",
        login_required(NotificationsView.as_view()),
        name="notifications-list"
    ),
    path(
        "<int:pk>/remove-notification/",
        login_required(HideNotificationView.as_view()),
        name="remove-notification"
    ),
]
