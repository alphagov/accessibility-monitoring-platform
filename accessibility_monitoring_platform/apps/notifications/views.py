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
    template_name: str = "view_notifications.html"
    context_object_name: str = "notifications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications: QuerySet[Notifications] = Notifications.objects.filter(user=self.request.user)
        context["notifications"] = notifications
        context["unread_notifications"] = len(notifications.filter(read=False))
        return context


class HideNotificationView(ListView):
    """
    Hides notification
    """
    model = Notifications

    def get(self, request, pk):
        """ Hides a notification """
        notifications: Notifications = Notifications.objects.get(pk=pk)
        if notifications.user.id == request.user.id:  # Checks whether the comment was posted by user
            notifications.read = True
            notifications.save()
            messages.success(request, "Notification marked as seen")
        else:
            messages.error(request, "An error occured")

        return HttpResponseRedirect(reverse_lazy("notifications:notifications-list"))


class UnhideNotificationView(ListView):
    """
    Unhides notification
    """
    model = Notifications

    def get(self, request, pk):
        """ Unhides a notification """
        notifications: Notifications = Notifications.objects.get(pk=pk)
        if notifications.user.id == request.user.id:  # Checks whether the comment was posted by user
            notifications.read = False
            notifications.save()
            messages.success(request, "Notification marked as unseen")
        else:
            messages.error(request, "An error occured")

        return HttpResponseRedirect(reverse_lazy("notifications:notifications-list"))
