"""Views for notifications app"""

from dataclasses import dataclass
from typing import ClassVar, List, Literal, Optional

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView

from ..cases.models import Case
from .models import Notification


class NotificationView(ListView):
    """
    Lists all notifications for user
    """

    model = Notification
    template_name: str = "notifications/view_notifications.html"
    context_object_name: str = "notifications"

    def get_queryset(self) -> QuerySet[Notification]:
        """Get reminders for logged in user"""
        notifications: QuerySet[Notification] = Notification.objects.filter(
            user=self.request.user
        )
        if self.request.GET.get("showing", "unread") == "unread":
            return notifications.filter(read=False)
        return notifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications: QuerySet[Notification] = self.get_queryset()
        context["showing"] = self.request.GET.get("showing", "unread")
        context["unread_notifications"] = len(notifications.filter(read=False))
        return context


class NotificationMarkAsReadView(ListView):
    """
    Mark notification as read
    """

    model = Notification

    def get(self, request, pk):
        """Hides a notification"""
        notification: Notification = Notification.objects.get(pk=pk)
        if (
            notification.user.id == request.user.id  # type: ignore
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

    model = Notification

    def get(self, request, pk):
        """Marks a notification as unread"""
        notification: Notification = Notification.objects.get(pk=pk)
        if (
            notification.user.id == request.user.id  # type: ignore
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


@dataclass
class Task:
    date: str
    case: Optional[Case] = None
    description: str = ""
    action_required: str = "n/a"
    edit_url: str = ""
    NOTIFICATION: ClassVar[str] = "notification"
    REMINDER: ClassVar[str] = "reminder"
    OVERDUE: ClassVar[str] = "overdue"
    POSTCASE: ClassVar[str] = "postcase"
    type: Literal[NOTIFICATION, REMINDER, OVERDUE, POSTCASE] = NOTIFICATION


class TaskListView(TemplateView):
    """
    Lists all tasks for user
    """

    template_name: str = "notifications/task_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications: QuerySet[Notification] = Notification.objects.filter(
            user=self.request.user, read=False
        )
        tasks: List[Task] = []
        for notification in notifications:
            path_elements: List[str] = notification.path.split("/")
            if path_elements[1] == "cases":
                case: Case = Case.objects.get(id=int(path_elements[2]))
            else:
                case: Optional[Case] = None
            tasks.append(
                Task(
                    date=notification.created_date,
                    case=case,
                    description=notification.body,
                    edit_url=notification.path,
                )
            )

        sorted_tasks: List[Task] = sorted(
            tasks,
            key=lambda task: (task.date),
        )
        context["tasks"] = sorted_tasks
        return context
