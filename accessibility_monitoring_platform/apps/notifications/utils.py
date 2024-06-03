"""Add notification function for notification app"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict

from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse

from ..audits.models import Retest
from ..cases.models import Case, CaseStatus, EqualityBodyCorrespondence
from .models import Notification, NotificationSetting, Option, Task


class EmailContextType(TypedDict):
    user: User
    list_description: str
    body: str
    path: str
    request: HttpRequest


def add_task(
    user: User,
    case: Case,
    type: Task.Type,
    description: str,
    list_description: str,
    request: HttpRequest,
) -> Task:
    """Adds notification to DB. Also handles email notifications."""
    task: Task = Task.objects.create(
        type=type,
        date=date.today(),
        case=case,
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
        path: str = reverse("cases:edit-qa-comments", kwargs={"pk": case.id})
    else:
        path: str = reverse("cases:edit-report-approved", kwargs={"pk": case.id})

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


def read_tasks(user: User, case: Case, type: Task.Type) -> None:
    """Mark tasks as read"""
    tasks: QuerySet[Notification] = Task.objects.filter(
        user=user, case=case, type=type, read=False
    )
    for task in tasks:
        task.read = True  # type: ignore
        task.save()


def get_overdue_cases(user_request: User) -> QuerySet[Case]:
    """Return cases with overdue correspondence actions"""
    if user_request.id:  # Pytest user has no id, skip process
        user: User = get_object_or_404(User, id=user_request.id)
        user_cases: QuerySet[Case] = Case.objects.filter(auditor=user)
        start_date: datetime = datetime(2020, 1, 1)
        end_date: datetime = datetime.now() - timedelta(days=1)
        seven_days_ago = date.today() - timedelta(days=7)

        seven_day_no_contact: QuerySet[Case] = user_cases.filter(
            status__status__icontains=CaseStatus.Status.REPORT_READY_TO_SEND,
            contact_details_found=Case.ContactDetailsFound.NOT_FOUND,
            seven_day_no_contact_email_sent_date__range=[start_date, seven_days_ago],
        )

        in_report_correspondence: QuerySet[Case] = user_cases.filter(
            Q(status__status="in-report-correspondence"),
            Q(
                Q(  # pylint: disable=unsupported-binary-operation
                    report_followup_week_1_due_date__range=[start_date, end_date],
                    report_followup_week_1_sent_date=None,
                )
                | Q(
                    report_followup_week_4_due_date__range=[start_date, end_date],
                    report_followup_week_4_sent_date=None,
                )
                | Q(
                    report_followup_week_4_sent_date__range=[start_date, seven_days_ago]
                )
            ),
        )

        in_probation_period: QuerySet[Case] = user_cases.filter(
            status__status__icontains="in-probation-period",
            report_followup_week_12_due_date__range=[start_date, end_date],
        )

        in_12_week_correspondence: QuerySet[Case] = user_cases.filter(
            Q(status__status__icontains="in-12-week-correspondence"),
            Q(
                Q(
                    twelve_week_1_week_chaser_due_date__range=[start_date, end_date],
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

        in_correspondence: QuerySet[Case] = (
            seven_day_no_contact
            | in_report_correspondence
            | in_probation_period
            | in_12_week_correspondence
        )

        in_correspondence: QuerySet[Case] = sorted(
            in_correspondence, key=lambda t: t.next_action_due_date  # type: ignore
        )
        return in_correspondence
    else:
        return Case.objects.none()


def build_overdue_task_options(case: Case) -> List[Option]:
    """Build list of options for overdue case task"""
    options: List[Option] = []
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    if case.status.status == CaseStatus.Status.REPORT_READY_TO_SEND:
        option: Option = Option(
            label="Seven day 'no contact details' response overdue",
            url=reverse("cases:edit-find-contact-details", kwargs=kwargs_case_pk),
        )
    elif case.status.status == CaseStatus.Status.IN_REPORT_CORES:
        option: Option = Option(
            label=case.in_report_correspondence_progress,
            url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
        )
    elif case.status.status == CaseStatus.Status.AWAITING_12_WEEK_DEADLINE:
        option: Option = Option(
            label="Overdue",
            url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
        )
    elif case.status.status == CaseStatus.Status.IN_12_WEEK_CORES:
        option: Option = Option(
            label=case.twelve_week_correspondence_progress,
            url=reverse("cases:edit-cores-overview", kwargs=kwargs_case_pk),
        )
    options.append(option)
    return options


def get_post_case_tasks(user: User) -> List[Task]:
    """
    Return list of tasks for unresolved equality body correspondence
    entries and incomplete equality body retests for a user.
    """
    tasks: List[Task] = []

    equality_body_correspondences: QuerySet[EqualityBodyCorrespondence] = (
        EqualityBodyCorrespondence.objects.filter(
            case__auditor=user,
            status=EqualityBodyCorrespondence.Status.UNRESOLVED,
        )
    )

    for equality_body_correspondence in equality_body_correspondences:
        task: Task = Task(
            type=Task.Type.POSTCASE,
            date=equality_body_correspondence.created.date(),
            case=equality_body_correspondence.case,
            description="Unresolved correspondence",
            action="View correspondence",
        )
        task.options = [
            Option(
                label="View correspondence",
                url=f"{equality_body_correspondence.get_absolute_url()}?view=unresolved",
            )
        ]
        tasks.append(task)

    retests: QuerySet[Retest] = Retest.objects.filter(
        is_deleted=False,
        case__auditor=user,
        retest_compliance_state=Retest.Compliance.NOT_KNOWN,
        id_within_case__gt=0,
    )

    for retest in retests:
        task: Task = Task(
            type=Task.Type.POSTCASE,
            date=retest.date_of_retest,
            case=retest.case,
            description="Incomplete retest",
            action="View retest",
        )
        task.options = [
            Option(
                label="View retest",
                url=retest.get_absolute_url(),
            )
        ]
        tasks.append(task)

    return tasks


def build_task_list(
    user: User,
    type: Optional[str] = None,
    read: Optional[str] = None,
    future: Optional[str] = None,
) -> List[Task]:
    """Build of tasks from database and items derived dynamically from Cases"""
    task_filter: Dict[str, Any] = {
        "user": user,
    }

    if type is not None:
        task_filter["type"] = type

    if read is None:
        task_filter["read"] = False
    elif read == "read":
        task_filter["read"] = True

    if future is None:
        task_filter["date__lte"] = date.today()

    tasks: List[Task] = list(Task.objects.filter(**task_filter))

    if type is None or type == Task.Type.OVERDUE:
        overdue_cases: QuerySet[Case] = get_overdue_cases(user_request=user)
        for overdue_case in overdue_cases:
            task: Task = Task(
                type=Task.Type.OVERDUE,
                date=overdue_case.next_action_due_date,
                case=overdue_case,
                description=overdue_case.status.get_status_display(),
                action="Chase overdue response",
            )
            task.options = build_overdue_task_options(case=overdue_case)
            tasks.append(task)

    if type is None or type == Task.Type.POSTCASE:
        tasks += get_post_case_tasks(user=user)

    sorted_tasks: List[Task] = sorted(
        tasks,
        key=lambda task: (task.date),
    )

    return sorted_tasks


def get_number_of_tasks(user: User) -> int:
    """Return number of tasks"""
    if user.id:  # If logged in user
        return len(build_task_list(user=user))
    return 0
