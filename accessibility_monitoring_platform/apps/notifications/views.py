"""Views for notifications app"""

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView

from .models import Notifications


class NotificationsView(ListView):
    """
    Lists all notifications for user
    """

    model = Notifications
    template_name: str = "notifications/view_notifications.html"
    context_object_name: str = "notifications"

    def get_queryset(self) -> QuerySet[Notifications]:
        """Get reminders for logged in user"""
        notifications: QuerySet[Notifications] = Notifications.objects.filter(
            user=self.request.user
        )
        if self.request.GET.get("showing", "unread") == "unread":
            return notifications.filter(read=False)
        return notifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications: QuerySet[Notifications] = self.get_queryset()
        context["showing"] = self.request.GET.get("showing", "unread")
        context["unread_notifications"] = len(notifications.filter(read=False))
        return context


class NotificationMarkAsReadView(ListView):
    """
    Mark notification as read
    """

    model = Notifications

    def get(self, request, pk):
        """Hides a notification"""
        notification: Notifications = Notifications.objects.get(pk=pk)
        if (
            notification.user.id == request.user.id
        ):  # Checks whether the comment was posted by user
            notification.read = True
            notification.save()
            messages.success(request, "Notification marked as seen")
        else:
            messages.error(request, "An error occured")

        showing_flag: str = self.request.GET.get("showing", "unread")
        return HttpResponseRedirect(
            f'{reverse_lazy("notifications:notifications-list")}?showing={showing_flag}'
        )


class NotificationMarkAsUnreadView(ListView):
    """
    Marks notification as unread
    """

    model = Notifications

    def get(self, request, pk):
        """Marks a notification as unread"""
        notification: Notifications = Notifications.objects.get(pk=pk)
        if (
            notification.user.id == request.user.id
        ):  # Checks whether the comment was posted by user
            notification.read = False
            notification.save()
            messages.success(request, "Notification marked as unseen")
        else:
            messages.error(request, "An error occured")

        showing_flag: str = self.request.GET.get("showing", "unread")
        return HttpResponseRedirect(
            f'{reverse_lazy("notifications:notifications-list")}?showing={showing_flag}'
        )
