"""Add notification function for notification app"""

from datetime import date, datetime, timedelta
from typing import Any, TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse

from ..audits.models import Retest
from ..simplified.models import (
    BaseCase,
    CaseStatus,
    EqualityBodyCorrespondence,
    SimplifiedCase,
)
from .models import Link, NotificationSetting, Task

TASK_LIST_PARAMS: list[str] = ["type", "read", "deleted", "future"]
TASK_LIST_READ_TIMEDELTA: timedelta = timedelta(days=7)


class EmailContextType(TypedDict):
    user: User
    list_description: str
    body: str
    path: str
    request: HttpRequest


def add_task(
    user: User,
    base_case: BaseCase,
    type: Task.Type,
    description: str,
    list_description: str,
    request: HttpRequest,
) -> Task:
    """Adds notification to database. Also handles email notifications."""
    task: Task = Task.objects.create(
        type=type,
        date=date.today(),
        base_case=base_case,
        user=user,
        description=description,
    )
    if NotificationSetting.objects.filter(pk=user.id).exists():  # type: ignore
        email_settings: NotificationSetting = NotificationSetting.objects.get(pk=user.id)  # type: ignore
    else:
        email_settings: NotificationSetting = NotificationSetting(
            user=user,
            email_notifications_enabled=False,
        )
        email_settings.save()

    if type == Task.Type.QA_COMMENT:
        path: str = reverse("simplified:edit-qa-comments", kwargs={"pk": base_case.id})
    else:
        path: str = reverse("simplified:edit-qa-approval", kwargs={"pk": base_case.id})

    if email_settings.email_notifications_enabled:
        context: EmailContextType = {
            "user": user,
            "list_description": list_description,
            "body": description,
            "path": path,
            "request": request,
        }
        template: str = get_template("notifications/notification_email.txt")
        content: str = template.render(context)  # type: ignore
        email: EmailMessage = EmailMessage(
            subject=f"You have a new notification in the monitoring platform : {list_description}",
            body=content,
            from_email="accessibility-monitoring-platform-contact-form@digital.cabinet-office.gov.uk",
            to=[user.email],
        )
        email.content_subtype = "html"
        email.send()
    return task


def mark_tasks_as_read(user: User, base_case: BaseCase, type: Task.Type) -> None:
    """Mark tasks as read"""
    tasks: QuerySet[Task] = Task.objects.filter(
        user=user, base_case=base_case, type=type, read=False
    )
    for task in tasks:
        task.read = True  # type: ignore
        task.save()


def exclude_cases_with_pending_reminders(
    cases: QuerySet[BaseCase],
) -> list[BaseCase]:
    """Return only cases without pending reminders"""
    today: date = date.today()
    cases_without_pending_reminders: list[BaseCase] = []
    for case in cases:
        if (
            Task.objects.filter(
                base_case=case, type=Task.Type.REMINDER, date__gte=today, read=False
            ).first()
            is None
        ):
            cases_without_pending_reminders.append(case)
    return cases_without_pending_reminders


def get_overdue_cases(user_request: User | None) -> list[SimplifiedCase]:
    """Return cases with overdue correspondence actions"""
    if user_request is not None:
        user: User = get_object_or_404(User, id=user_request.id)
        cases: QuerySet[SimplifiedCase] = SimplifiedCase.objects.filter(auditor=user)
    else:
        cases: QuerySet[SimplifiedCase] = SimplifiedCase.objects.filter(archive="")
    start_date: datetime = datetime(2020, 1, 1)
    end_date: datetime = datetime.now()
    seven_days_ago = date.today() - timedelta(days=7)

    seven_day_no_contact: QuerySet[SimplifiedCase] = cases.filter(
        Q(status__icontains=CaseStatus.Status.REPORT_READY_TO_SEND),
        Q(enable_correspondence_process=True),
        Q(
            Q(
                seven_day_no_contact_email_sent_date__range=[
                    start_date,
                    seven_days_ago,
                ],
                no_contact_one_week_chaser_sent_date=None,
                no_contact_four_week_chaser_sent_date=None,
                no_contact_one_week_chaser_due_date__range=[start_date, end_date],
            )
            | Q(
                no_contact_one_week_chaser_due_date__range=[
                    start_date,
                    end_date,
                ],
                no_contact_one_week_chaser_sent_date=None,
            )
            | Q(
                no_contact_four_week_chaser_due_date__range=[
                    start_date,
                    end_date,
                ],
                no_contact_four_week_chaser_sent_date=None,
            )
        ),
    )

    in_report_correspondence: QuerySet[SimplifiedCase] = cases.filter(
        Q(status=CaseStatus.Status.IN_REPORT_CORES),
        Q(
            Q(  # pylint: disable=unsupported-binary-operation
                report_followup_week_1_due_date__range=[
                    start_date,
                    end_date,
                ],
                report_followup_week_1_sent_date=None,
            )
            | Q(
                report_followup_week_4_due_date__range=[
                    start_date,
                    end_date,
                ],
                report_followup_week_4_sent_date=None,
            )
            | Q(
                report_followup_week_4_sent_date__range=[
                    start_date,
                    seven_days_ago,
                ]
            )
        ),
    )

    in_probation_period: QuerySet[SimplifiedCase] = cases.filter(
        status__icontains=CaseStatus.Status.AWAITING_12_WEEK_DEADLINE,
        report_followup_week_12_due_date__range=[start_date, end_date],
    )

    in_12_week_correspondence: QuerySet[SimplifiedCase] = cases.filter(
        Q(status__icontains=CaseStatus.Status.AFTER_12_WEEK_CORES),
        Q(
            Q(
                twelve_week_1_week_chaser_due_date__range=[
                    start_date,
                    end_date,
                ],
                twelve_week_1_week_chaser_sent_date=None,
            )
            | Q(
                twelve_week_1_week_chaser_sent_date__range=[
                    start_date,
                    seven_days_ago,
                ],
            )
        ),
    )

    in_correspondence: QuerySet[SimplifiedCase] = (
        seven_day_no_contact
        | in_report_correspondence
        | in_probation_period
        | in_12_week_correspondence
    )

    overdue_cases: list[SimplifiedCase] = exclude_cases_with_pending_reminders(
        cases=in_correspondence
    )

    sorted_overdue_cases: list[SimplifiedCase] = sorted(
        overdue_cases, key=lambda t: t.next_action_due_date  # type: ignore
    )

    return sorted_overdue_cases


def get_post_case_tasks(user: User) -> list[Task]:
    """
    Return list of tasks for unresolved equality body correspondence
    entries and incomplete equality body retests for a user.
    """
    tasks: list[Task] = []

    equality_body_correspondences: QuerySet[EqualityBodyCorrespondence] = (
        EqualityBodyCorrespondence.objects.filter(
            simplified_case__auditor=user,
            status=EqualityBodyCorrespondence.Status.UNRESOLVED,
        )
    )

    today: date = date.today()

    for equality_body_correspondence in equality_body_correspondences:
        if (
            Task.objects.filter(
                base_case=equality_body_correspondence.simplified_case,
                type=Task.Type.REMINDER,
                date__gte=today,
            ).first()
            is None
        ):
            task: Task = Task(
                type=Task.Type.POSTCASE,
                date=equality_body_correspondence.created.date(),
                base_case=equality_body_correspondence.simplified_case,
                description="Unresolved correspondence",
                action="View correspondence",
            )
            task.options = [
                Link(
                    label="View correspondence",
                    url=f"{equality_body_correspondence.get_absolute_url()}?view=unresolved",
                )
            ]
            tasks.append(task)

    retests: QuerySet[Retest] = Retest.objects.filter(
        is_deleted=False,
        simplified_case__auditor=user,
        retest_compliance_state=Retest.Compliance.NOT_KNOWN,
        id_within_case__gt=0,
    )

    for retest in retests:
        if (
            Task.objects.filter(
                base_case=retest.simplified_case,
                type=Task.Type.REMINDER,
                date__gte=today,
            ).first()
            is None
        ):
            task: Task = Task(
                type=Task.Type.POSTCASE,
                date=retest.date_of_retest,
                base_case=retest.simplified_case,
                description="Incomplete retest",
                action="View retest",
            )
            task.options = [
                Link(
                    label="View retest",
                    url=retest.get_absolute_url(),
                )
            ]
            tasks.append(task)

    return tasks


def build_task_list(user: User | None, **kwargs: dict[str, str]) -> list[Task]:
    """Build list of tasks from database and items derived dynamically from Cases"""
    task_filter: dict[str, Any] = {
        "read": False,
    }

    if user is not None:
        task_filter["user"] = user

    type: str | None = kwargs.get("type")

    read: bool = kwargs.get("read") is not None
    if type is not None:
        task_filter["type"] = type
    if read or kwargs.get("deleted") is not None:
        task_filter["read"] = True
        task_filter["date__gte"] = date.today() - TASK_LIST_READ_TIMEDELTA
    elif kwargs.get("future") is None:
        task_filter["date__lte"] = date.today()

    tasks: list[Task] = list(Task.objects.filter(**task_filter))

    if type is None or type == Task.Type.OVERDUE:
        overdue_cases: QuerySet[SimplifiedCase] = get_overdue_cases(user_request=user)
        for overdue_case in overdue_cases:
            task: Task = Task(
                type=Task.Type.OVERDUE,
                date=overdue_case.next_action_due_date,
                base_case=overdue_case,
                description=overdue_case.get_status_display(),
                action="Chase overdue response",
            )
            task.options = [overdue_case.overdue_link]
            tasks.append(task)

    if type is None or type == Task.Type.POSTCASE:
        tasks += get_post_case_tasks(user=user)

    sorted_tasks: list[Task] = sorted(
        tasks,
        key=lambda task: (task.date),
        reverse=read,
    )

    return sorted_tasks


def get_number_of_tasks(user: User) -> int:
    """Return number of tasks"""
    if user.id:  # If logged in user
        return len(build_task_list(user=user))
    return 0


def get_tasks_by_type_count(tasks: list[Task], type: Task.Type) -> int:
    """Return the number of tasks of a specific type"""
    return len([task for task in tasks if task.type == type])


def get_task_type_counts(tasks: list[Task]) -> dict[str, int]:
    """Return the number of tasks of each type"""
    return {
        "qa_comment": get_tasks_by_type_count(tasks=tasks, type=Task.Type.QA_COMMENT),
        "report_approved": get_tasks_by_type_count(
            tasks=tasks, type=Task.Type.REPORT_APPROVED
        ),
        "reminder": get_tasks_by_type_count(tasks=tasks, type=Task.Type.REMINDER),
        "overdue": get_tasks_by_type_count(tasks=tasks, type=Task.Type.OVERDUE),
        "postcase": get_tasks_by_type_count(tasks=tasks, type=Task.Type.POSTCASE),
    }
