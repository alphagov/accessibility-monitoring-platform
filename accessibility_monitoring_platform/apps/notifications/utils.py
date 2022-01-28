"""Add notification function for notification app"""
from typing import TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.http import HttpRequest
from django.template.loader import get_template

from .models import Notifications, NotificationsSettings


class EmailContextType(TypedDict):
    user: User
    list_description: str
    body: str
    path: str
    request: HttpRequest


def add_notification(
    user: User,
    body: str,
    path: str,
    list_description: str,
    request: HttpRequest
) -> Notifications:
    """Adds notification to DB. Also handles email notifications.

    Parameters
    ----------
    user : User
        user object
    body : str
        Message to user for notification
    path : str
        The path where the notification exists
    list_description : str
        Description of the location of the notification
    request : HttpRequest
        Django request

    Returns
    -------
    Notifications
        Notifications model
    """
    notification: Notifications = Notifications(
        user=user,
        body=body,
        path=path,
        list_description=list_description
    )
    notification.save()
    if NotificationsSettings.objects.filter(pk=user.id).exists():  # type: ignore
        email_settings: NotificationsSettings = NotificationsSettings.objects.get(pk=user.id)  # type: ignore
    else:
        email_settings: NotificationsSettings = NotificationsSettings(
            user=user,
            email_notifications_enabled=False,
        )
        email_settings.save()

    if email_settings.email_notifications_enabled:
        context: EmailContextType = {
            "user": user,
            "list_description": list_description,
            "body": body,
            "path": path,
            "request": request,
        }
        template: str = get_template("notifications/email.txt")
        content: str = template.render(context)  # type: ignore
        email: EmailMessage = EmailMessage(
            subject=f"You have a new notification in the monitoring platform : {list_description}",
            body=content,
            from_email="accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk",
            to=[user.email],
        )
        email.content_subtype = "html"
        email.send()
    return notification


def read_notification(request: HttpRequest) -> None:
    """Will read the path and user from the request and remove the notification
    if a notification exists

    Parameters
    ----------
    request : HttpRequest
    """
    notifications: QuerySet[Notifications] = Notifications.objects.filter(
        user=request.user,
        path=request.path,
        read=False
    )
    for notification in notifications:
        notification.read = True  # type: ignore
        notification.save()
