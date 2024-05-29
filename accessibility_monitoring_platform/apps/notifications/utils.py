"""Add notification function for notification app"""

from typing import List, TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import QuerySet
from django.http import HttpRequest
from django.template.loader import get_template

from ..cases.models import Case
from ..cases.utils import PostCaseAlert, get_post_case_alerts
from ..overdue.utils import get_overdue_cases
from .models import Notification, NotificationSetting, Option, Task


class EmailContextType(TypedDict):
    user: User
    list_description: str
    body: str
    path: str
    request: HttpRequest


def add_notification(
    user: User, body: str, path: str, list_description: str, request: HttpRequest
) -> Notification:
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
    notification: Notification = Notification(
        user=user, body=body, path=path, list_description=list_description
    )
    notification.save()
    if NotificationSetting.objects.filter(pk=user.id).exists():  # type: ignore
        email_settings: NotificationSetting = NotificationSetting.objects.get(pk=user.id)  # type: ignore
    else:
        email_settings: NotificationSetting = NotificationSetting(
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
    notifications: QuerySet[Notification] = Notification.objects.filter(
        user=request.user, path=request.path, read=False
    )
    for notification in notifications:
        notification.read = True  # type: ignore
        notification.save()


def get_number_of_unread_notifications(user: User) -> int:
    """Return the number of unread notifications for the user"""
    if user.id:
        return Notification.objects.filter(user=user, read=False).count()
    return 0


def build_task_list(user: User) -> List[Task]:
    """Build of tasks from database and items derived dynamically from Cases"""
    tasks: List[Task] = list(Task.objects.filter(user=user, read=False))
    overdue_cases: QuerySet[Case] = get_overdue_cases(user_request=user)
    for overdue_case in overdue_cases:
        tasks.append(
            Task(
                type=Task.Type.OVERDUE,
                date=overdue_case.next_action_due_date,
                case=overdue_case,
                description=overdue_case.status.get_status_display(),
                action="Chase overdue response",
            )
        )
    post_case_alerts: List[PostCaseAlert] = get_post_case_alerts(user=user)
    for post_case_alert in post_case_alerts:
        task: Task = Task(
            type=Task.Type.POSTCASE,
            date=post_case_alert.date,
            case=post_case_alert.case,
            description=post_case_alert.description,
            action=post_case_alert.absolute_url_label,
        )
        task.options = [
            Option(
                label=post_case_alert.absolute_url_label,
                url=post_case_alert.absolute_url,
            ),
        ]
        tasks.append(task)

    sorted_tasks: List[Task] = sorted(
        tasks,
        key=lambda task: (task.date),
    )

    return sorted_tasks
