"""Add notification function for notification app"""
from typing import Any, TypedDict
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from .models import Notifications, NotificationsSettings
from django.contrib.auth.models import User
from django.http import HttpRequest


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

    email_settings: NotificationsSettings = NotificationsSettings.objects.get(pk=user.id)

    if email_settings.email_notifications_enabled:
        plaintext: Any = get_template("email.txt")
        htmly: Any = get_template("email.html")
        context: EmailContextType = {
            "user": user,
            "list_description": list_description,
            "body": body,
            "path": path,
            "request": request,
        }
        text_content: str = plaintext.render(context)
        html_content: str = htmly.render(context)
        subject: str = f"You have a new notification in the monitoring platform : {list_description}"
        msg: EmailMultiAlternatives = EmailMultiAlternatives(
            subject,
            text_content,
            from_email="accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk",
            to=[user.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    return notification
