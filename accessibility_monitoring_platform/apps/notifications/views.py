"""Views for notifications app"""
from typing import Any, Dict

from django.views.generic import ListView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
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
        view_all: bool = False
        if (
            self.request.GET
            and self.request.GET["view"]
            and self.request.GET["view"] == "View all notifications"
        ):
            view_all = True

        filter_dict: Dict[str, Any] = {"user": self.request.user}

        if not view_all:
            filter_dict["read"] = False

        notifications = Notifications.objects.filter(**filter_dict)

        context["notifications"] = notifications
        context["show_all_notifications"] = view_all
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
