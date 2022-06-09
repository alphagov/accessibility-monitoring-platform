"""Template tag for notifications"""
from django import template
from django.db.models import QuerySet
from django.http import HttpRequest
from ..models import Notification

register = template.Library()


@register.simple_tag()
def notifications_count(request: HttpRequest) -> int:
    """Returns the number of notifications for the user

    Parameters
    ----------
    request : HttpRequest

    Returns
    -------
    int
        Number of notifications
    """
    count: QuerySet[Notification] = Notification.objects.filter(
        user=request.user,
        read=False,
    )
    return len(count)


@register.simple_tag()
def read_notification(request: HttpRequest) -> str:
    """Will read the path and user from the request and remove the notification
    if a notification exists

    Parameters
    ----------
    request : HttpRequest

    Returns
    -------
    str
        Returns empty string to avoid outputting to html template
    """
    notifications: QuerySet[Notification] = Notification.objects.filter(
        user=request.user, path=request.path, read=False
    )
    for notification in notifications:
        notification.read = True
        notification.save()
    return ""
