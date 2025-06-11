"""Tests - test for notifications template tags"""

from datetime import date, datetime, timedelta

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse

from ...audits.models import Retest
from ...cases.models import BaseCase, CaseCompliance, EqualityBodyCorrespondence
from ...cases.utils import create_case_and_compliance
from ...cases.views import (
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
)
from ...common.models import Boolean, Link
from ..models import NotificationSetting, Task
from ..utils import (
    add_task,
    build_task_list,
    exclude_cases_with_pending_reminders,
    get_number_of_tasks,
    get_overdue_cases,
    get_post_case_tasks,
    get_task_type_counts,
    get_tasks_by_type_count,
    mark_tasks_as_read,
)

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
ONE_WEEK_AGO = TODAY - timedelta(days=7)
TWO_WEEKS_AGO = TODAY - timedelta(days=14)
THREE_WEEKS_AGO = TODAY - timedelta(days=21)
FOUR_WEEKS_AGO = TODAY - timedelta(days=28)
FIVE_WEEKS_AGO = TODAY - timedelta(days=35)
ELEVEN_WEEKS_AGO = TODAY - timedelta(days=77)
TWELVE_WEEKS_AGO = TODAY - timedelta(days=84)
THIRTEEN_WEEKS_AGO = TODAY - timedelta(days=91)
FOURTEEN_WEEKS_AGO = TODAY - timedelta(days=98)


def create_case(user: User) -> BaseCase:
    base_case: BaseCase = create_case_and_compliance(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_draft_url="https://www.report-draft.com",
        report_review_status=Boolean.YES,
        reviewer=user,
        report_approved_status=BaseCase.ReportApprovedStatus.APPROVED,
        report_final_pdf_url="https://www.report-pdf.com",
        report_final_odt_url="https://www.report-odt.com",
    )
    return base_case


@pytest.mark.django_db
def test_mark_tasks_as_read_marks_task_as_read(rf):
    """test to check if mark_tasks_as_read function marks tasks as read"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    base_case: BaseCase = BaseCase.objects.create()

    task: Task = Task.objects.create(
        date=date.today(), user=user, base_case=base_case, type=Task.Type.QA_COMMENT
    )

    assert not task.read

    mark_tasks_as_read(user=user, base_case=base_case, type=Task.Type.QA_COMMENT)

    task_from_db: Task = Task.objects.get(id=task.id)  # type: ignore

    assert task_from_db.read


@pytest.mark.django_db
@pytest.mark.parametrize(
    "type",
    [Task.Type.QA_COMMENT, Task.Type.REPORT_APPROVED],
)
def test_add_task_creates_task_and_sends_email(type, mailoutbox, rf):
    """test to check if add_task adds task and sends email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user)
    base_case: BaseCase = BaseCase.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        base_case=base_case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Task | None = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"

    assert len(mailoutbox) == 1
    assert (
        mailoutbox[0].subject
        == "You have a new notification in the monitoring platform : There is a notification"
    )


@pytest.mark.django_db
def test_add_task_creates_task_and_sends_no_email(mailoutbox, rf):
    """test to check if add_task adds task and doesn't send email"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    NotificationSetting.objects.create(user=user, email_notifications_enabled=False)
    base_case: BaseCase = BaseCase.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        base_case=base_case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Task | None = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"

    assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_add_task_creates_new_email_notification_model_when_null(mailoutbox, rf):
    """
    Test to see if add_task will create a NotificationSetting
    model when none exists
    """
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    base_case: BaseCase = BaseCase.objects.create()

    assert NotificationSetting.objects.all().first() is None

    add_task(
        user=user,
        base_case=base_case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Task | None = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"
    assert len(mailoutbox) == 0

    notification_setting: NotificationSetting | None = (
        NotificationSetting.objects.all().first()
    )

    assert notification_setting is not None
    assert notification_setting.user.email == user.email
    assert notification_setting.email_notifications_enabled is False


@pytest.mark.django_db
def test_get_post_case_tasks():
    """Test returning unresolved correspondence and incomplate retests"""
    user: User = User.objects.create()

    assert len(get_post_case_tasks(user=user)) == 0

    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(base_case=base_case)
    )

    post_case_tasks: list[Task] = get_post_case_tasks(user=user)

    assert len(post_case_tasks) == 1

    post_case_task: Task = post_case_tasks[0]

    assert post_case_task.type == Task.Type.POSTCASE
    assert post_case_task.date == equality_body_correspondence.created.date()
    assert post_case_task.base_case == base_case
    assert post_case_task.description == "Unresolved correspondence"
    assert len(post_case_task.options) == 1

    option: Link = post_case_task.options[0]

    assert (
        option.url
        == f"{equality_body_correspondence.get_absolute_url()}?view=unresolved"
    )
    assert option.label == "View correspondence"

    equality_body_correspondence.status = EqualityBodyCorrespondence.Status.RESOLVED
    equality_body_correspondence.save()

    assert len(get_post_case_tasks(user=user)) == 0

    retest: Retest = Retest.objects.create(base_case=base_case)

    post_case_tasks: list[Task] = get_post_case_tasks(user=user)

    assert len(post_case_tasks) == 1

    post_case_task: Task = post_case_tasks[0]

    assert post_case_task.type == Task.Type.POSTCASE
    assert post_case_task.date == retest.date_of_retest
    assert post_case_task.base_case == base_case
    assert post_case_task.description == "Incomplete retest"

    option: Link = post_case_task.options[0]

    assert option.url == retest.get_absolute_url()
    assert option.label == "View retest"

    retest.retest_compliance_state = Retest.Compliance.COMPLIANT
    retest.save()

    assert len(get_post_case_tasks(user=user)) == 0


@pytest.mark.django_db
def test_report_ready_to_send_seven_day_no_contact():
    """
    Show overdue if report is ready to send and seven day no
    contact email sent date is more than seven days ago.
    """
    user: User = User.objects.create()

    base_case: BaseCase = create_case(user)

    assert len(get_overdue_cases(user)) == 0

    base_case.enable_correspondence_process = True
    base_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    base_case.no_contact_one_week_chaser_due_date = YESTERDAY
    base_case.save()

    assert len(get_overdue_cases(user)) == 1


@pytest.mark.django_db
def test_report_ready_to_send_seven_day_no_contact_for_all_users():
    """
    Show overdue if report is ready to send and seven day no
    contact email sent date is more than seven days ago for all users.
    """
    user_1: User = User.objects.create(username="user1", email="email1@example.com")
    case_1: BaseCase = create_case(user_1)
    user_2: User = User.objects.create(username="user2", email="email2@example.com")
    case_2: BaseCase = create_case(user_2)

    assert len(get_overdue_cases(None)) == 0

    case_1.enable_correspondence_process = True
    case_1.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case_1.no_contact_one_week_chaser_due_date = YESTERDAY
    case_1.save()
    case_2.enable_correspondence_process = True
    case_2.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case_2.no_contact_one_week_chaser_due_date = YESTERDAY
    case_2.save()

    assert len(get_overdue_cases(None)) == 2


@pytest.mark.django_db
def test_report_ready_to_send_no_contact_one_week_chaser_due():
    """
    Show overdue if report is ready to send and no contact
    1-week chaser due date has been reached but not sent
    """
    user: User = User.objects.create()

    base_case: BaseCase = create_case(user)
    base_case.enable_correspondence_process = True
    base_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    base_case.no_contact_one_week_chaser_sent_date = TODAY
    base_case.save()

    assert len(get_overdue_cases(user)) == 0

    base_case.no_contact_one_week_chaser_sent_date = None
    base_case.no_contact_one_week_chaser_due_date = TODAY
    base_case.no_contact_one_week_chaser_due_date = YESTERDAY
    base_case.save()

    assert len(get_overdue_cases(user)) == 1


@pytest.mark.django_db
def test_report_ready_to_send_no_contact_one_week_chaser_due_for_all_users():
    """
    Show overdue if report is ready to send and no contact
    1-week chaser due date has been reached but not sent for all users.
    """
    user_1: User = User.objects.create(username="user1", email="email1@example.com")
    case_1: BaseCase = create_case(user_1)
    case_1.enable_correspondence_process = True
    case_1.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case_1.no_contact_one_week_chaser_sent_date = TODAY
    user_2: User = User.objects.create(username="user2", email="email2@example.com")
    case_2: BaseCase = create_case(user_2)
    case_2.enable_correspondence_process = True
    case_2.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case_2.no_contact_one_week_chaser_sent_date = TODAY

    assert len(get_overdue_cases(None)) == 0

    case_1.no_contact_one_week_chaser_sent_date = None
    case_1.no_contact_one_week_chaser_due_date = TODAY
    case_1.save()
    case_2.no_contact_one_week_chaser_sent_date = None
    case_2.no_contact_one_week_chaser_due_date = TODAY
    case_2.save()

    assert len(get_overdue_cases(None)) == 2


@pytest.mark.django_db
def test_report_ready_to_send_no_contact_four_week_chaser_due():
    """
    Show overdue if report is ready to send and no contact
    4-week chaser due date has been reached but not sent
    """
    user: User = User.objects.create()

    base_case: BaseCase = create_case(user)
    base_case.enable_correspondence_process = True
    base_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    base_case.no_contact_four_week_chaser_sent_date = TODAY
    base_case.save()

    assert len(get_overdue_cases(user)) == 0
    assert len(get_overdue_cases(None)) == 0

    base_case.no_contact_four_week_chaser_sent_date = None
    base_case.no_contact_four_week_chaser_due_date = TODAY
    base_case.save()

    assert len(get_overdue_cases(user)) == 1
    assert len(get_overdue_cases(None)) == 1


@pytest.mark.django_db
def test_returns_no_overdue_cases():
    """Creates seven cases that are all in correspondence with the PSB but require no further actions.
    Should return an empty queryset as none are overdue.
    """
    user: User = User.objects.create()

    # BaseCase #1 - ready to be sent
    base_case: BaseCase = create_case(user)

    # BaseCase #2 - Sent, waiting for one week followup
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = TODAY
    base_case.save()

    # BaseCase #3 - Sent one week followup, waiting for four week followup
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = ONE_WEEK_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_followup_week_1_sent_date = YESTERDAY
    base_case.save()

    # BaseCase #4 - Sent four week followup, waiting for five day deadline
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = FOUR_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    base_case.report_followup_week_4_sent_date = YESTERDAY
    base_case.save()

    # BaseCase #5 - Report has been acknolwedged, waiting for 12-week deadline
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = FOUR_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    base_case.report_followup_week_4_sent_date = YESTERDAY
    base_case.report_acknowledged_date = datetime.now()
    base_case.save()

    # BaseCase #6 - BaseCase is past 12-week deadline, update requested
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = TWELVE_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_acknowledged_date = ELEVEN_WEEKS_AGO
    base_case.twelve_week_update_requested_date = TODAY
    base_case.save()

    # BaseCase #7 - BaseCase is past 1 week deadline for update, 1 week chaser requested
    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = THIRTEEN_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_acknowledged_date = TWELVE_WEEKS_AGO
    base_case.twelve_week_update_requested_date = ONE_WEEK_AGO
    base_case.twelve_week_1_week_chaser_sent_date = TODAY
    base_case.save()

    assert list(get_overdue_cases(user)) == []
    assert list(get_overdue_cases(None)) == []


@pytest.mark.django_db
def test_in_report_correspondence_week_1_overdue():
    """Creates two cases; one that is not overdue and another that requires a one-week chaser."""
    user: User = User.objects.create()
    new_case: BaseCase = create_case(user)
    new_case.report_sent_date = datetime.now()
    new_case.save()

    base_case: BaseCase = create_case(user)

    base_case.report_sent_date = ONE_WEEK_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        base_case.in_report_correspondence_progress.label
        == "1-week follow-up to report due"
    )
    assert base_case.in_report_correspondence_progress.url == reverse(
        "simplified:edit-report-one-week-followup", kwargs={"pk": base_case.id}
    )


@pytest.mark.django_db
def test_in_report_correspondence_week_4_overdue():
    """Creates two cases; one that is not overdue and another that requires a four-week chaser."""
    user: User = User.objects.create()
    create_case(user)

    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = FOUR_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        base_case.in_report_correspondence_progress.label
        == "4-week follow-up to report due"
    )
    assert base_case.in_report_correspondence_progress.url == reverse(
        "simplified:edit-report-four-week-followup", kwargs={"pk": base_case.id}
    )


@pytest.mark.django_db
def test_in_report_correspondence_psb_overdue_after_four_week_reminder():
    """Creates two cases; one that is not overdue and another that needs to be moved to equality body correspondence."""
    user: User = User.objects.create()
    create_case(user)

    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = FIVE_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_followup_week_1_sent_date = FOUR_WEEKS_AGO
    base_case.report_followup_week_4_sent_date = ONE_WEEK_AGO
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        base_case.in_report_correspondence_progress.label
        == "4-week follow-up to report sent, base_case needs to progress"
    )
    assert base_case.in_report_correspondence_progress.url == reverse(
        "simplified:edit-report-acknowledged", kwargs={"pk": base_case.id}
    )


@pytest.mark.django_db
def test_in_probation_period_overdue():
    """Creates two cases; one that is not overdue and another that needs to be moved to equality body correspondence."""
    user: User = User.objects.create()
    create_case(user)

    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = THIRTEEN_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_acknowledged_date = TWELVE_WEEKS_AGO
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1


@pytest.mark.django_db
def test_in_12_week_correspondence_1_week_followup_overdue():
    """
    Creates two cases; one that is not overdue and another that needs
    a one-week followup after the 12-week waiting period.
    """
    user: User = User.objects.create()
    create_case(user)

    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = THIRTEEN_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_acknowledged_date = THIRTEEN_WEEKS_AGO
    base_case.twelve_week_update_requested_date = ONE_WEEK_AGO
    base_case = calculate_twelve_week_chaser_dates(
        base_case, base_case.twelve_week_update_requested_date
    )
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert base_case.twelve_week_correspondence_progress.label == "1-week follow-up due"
    assert base_case.twelve_week_correspondence_progress.url == reverse(
        "simplified:edit-12-week-one-week-followup-final", kwargs={"pk": base_case.id}
    )


@pytest.mark.django_db
def test_in_12_week_correspondence_psb_overdue_after_one_week_reminder():
    """
    Creates two cases; one that is not overdue and another that needs
    to move to final decision after the 12-week waiting period.
    """
    user: User = User.objects.create()
    create_case(user)

    base_case: BaseCase = create_case(user)
    base_case.report_sent_date = FOURTEEN_WEEKS_AGO
    base_case = calculate_report_followup_dates(base_case, base_case.report_sent_date)
    base_case.report_acknowledged_date = FOURTEEN_WEEKS_AGO
    base_case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    base_case = calculate_twelve_week_chaser_dates(
        base_case, base_case.twelve_week_update_requested_date
    )
    base_case.twelve_week_1_week_chaser_sent_date = ONE_WEEK_AGO
    base_case.save()

    assert len(BaseCase.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        base_case.twelve_week_correspondence_progress.label
        == "1-week follow-up sent, base_case needs to progress"
    )
    assert base_case.twelve_week_correspondence_progress.url == reverse(
        "simplified:edit-12-week-update-request-ack", kwargs={"pk": base_case.id}
    )


@pytest.mark.django_db
def test_pending_reminder_removes_overdue():
    """Test overdue cases with pending reminders are excluded"""
    user: User = User.objects.create()
    base_case: BaseCase = create_case(user)
    base_case.enable_correspondence_process = True
    base_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    base_case.no_contact_one_week_chaser_due_date = YESTERDAY
    base_case.save()

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 1

    Task.objects.create(
        type=Task.Type.REMINDER,
        user=user,
        base_case=base_case,
        date=date.today() + timedelta(days=1),
    )

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 0


@pytest.mark.django_db
def test_build_task_list_empty():
    """Test build_task_list finds no tasks"""
    user: User = User.objects.create()

    assert build_task_list(user=user) == []


@pytest.mark.django_db
def test_build_task_list_qa_comment():
    """Test build_task_list finds QA comment task"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        base_case=base_case,
        user=user,
    )

    assert build_task_list(user=user) == [task]


@pytest.mark.django_db
def test_build_task_list_report_approved():
    """Test build_task_list finds Report approved task"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REPORT_APPROVED,
        date=date.today(),
        base_case=base_case,
        user=user,
    )

    assert build_task_list(user=user) == [task]


@pytest.mark.django_db
def test_build_task_list_reverse_sorts_read():
    """
    Test build_task_list sorts read tasks by newest first
    """
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    task_1: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today() - timedelta(days=1),
        base_case=base_case,
        user=user,
        read=True,
    )
    task_2: Task = Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        base_case=base_case,
        user=user,
        read=True,
    )

    assert build_task_list(user=user, read="true") == [task_2, task_1]


@pytest.mark.django_db
def test_build_task_list_reminder():
    """Test build_task_list finds reminder task"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    task: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        date=date.today(),
        base_case=base_case,
        user=user,
    )

    assert build_task_list(user=user) == [task]


@pytest.mark.django_db
def test_build_task_list_overdue():
    """Test build_task_list finds overdue task"""
    user: User = User.objects.create()
    base_case: BaseCase = create_case(user)
    base_case.enable_correspondence_process = True
    base_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    base_case.no_contact_one_week_chaser_due_date = YESTERDAY
    base_case.save()

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 1

    task: Task = tasks[0]

    assert task.type == Task.Type.OVERDUE


@pytest.mark.django_db
def test_build_task_list_postcase():
    """Test build_task_list finds post base_case task"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    EqualityBodyCorrespondence.objects.create(base_case=base_case)

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 1

    task: Task = tasks[0]

    assert task.type == Task.Type.POSTCASE


@pytest.mark.django_db
def test_pending_reminder_removes_postcase():
    """
    Test cases with pending reminders are excluded from being post
    base_case tasks
    """
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    EqualityBodyCorrespondence.objects.create(base_case=base_case)
    Retest.objects.create(
        base_case=base_case,
        retest_compliance_state=Retest.Compliance.NOT_KNOWN,
        id_within_case=1,
    )

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 2

    Task.objects.create(
        type=Task.Type.REMINDER,
        user=user,
        base_case=base_case,
        date=date.today() + timedelta(days=1),
    )

    tasks: list[Task] = build_task_list(user=user)

    assert len(tasks) == 0


@pytest.mark.django_db
def test_get_number_of_tasks_empty():
    """Test get_number_of_tasks finds no tasks"""
    user: User = User.objects.create()

    assert get_number_of_tasks(user=user) == 0


@pytest.mark.django_db
def test_get_number_of_tasks():
    """Test get_number_of_tasks"""
    user: User = User.objects.create()
    base_case: BaseCase = BaseCase.objects.create(auditor=user)
    Task.objects.create(
        type=Task.Type.QA_COMMENT,
        date=date.today(),
        base_case=base_case,
        user=user,
    )

    assert get_number_of_tasks(user=user) == 1


def test_get_tasks_by_type_count():
    """Test filtering tasks by type and counting how many there are"""
    tasks: list[Task] = [
        Task(type=Task.Type.QA_COMMENT),
        Task(type=Task.Type.QA_COMMENT),
        Task(type=Task.Type.REMINDER),
    ]

    assert get_tasks_by_type_count(tasks=tasks, type=Task.Type.QA_COMMENT) == 2


def test_get_task_type_counts():
    """Test counting the numbers of tasks of each type"""
    tasks: list[Task] = []

    assert get_task_type_counts(tasks=tasks) == {
        "qa_comment": 0,
        "report_approved": 0,
        "reminder": 0,
        "overdue": 0,
        "postcase": 0,
    }

    tasks: list[Task] = [
        Task(type=Task.Type.QA_COMMENT),
        Task(type=Task.Type.REPORT_APPROVED),
        Task(type=Task.Type.REPORT_APPROVED),
        Task(type=Task.Type.REMINDER),
        Task(type=Task.Type.REMINDER),
        Task(type=Task.Type.REMINDER),
        Task(type=Task.Type.OVERDUE),
        Task(type=Task.Type.OVERDUE),
        Task(type=Task.Type.OVERDUE),
        Task(type=Task.Type.OVERDUE),
        Task(type=Task.Type.POSTCASE),
        Task(type=Task.Type.POSTCASE),
        Task(type=Task.Type.POSTCASE),
        Task(type=Task.Type.POSTCASE),
        Task(type=Task.Type.POSTCASE),
    ]

    assert get_task_type_counts(tasks=tasks) == {
        "qa_comment": 1,
        "report_approved": 2,
        "reminder": 3,
        "overdue": 4,
        "postcase": 5,
    }


@pytest.mark.django_db
def test_exclude_cases_with_pending_reminders():
    """
    Test exclude_cases_with_pending_reminders returns cases
    without pending reminders
    """

    assert exclude_cases_with_pending_reminders(cases=[]) == []

    base_case: BaseCase = BaseCase.objects.create()
    case_to_exclude: BaseCase = BaseCase.objects.create()

    assert exclude_cases_with_pending_reminders(cases=[base_case, case_to_exclude]) == [
        base_case,
        case_to_exclude,
    ]

    user: User = User.objects.create()
    Task.objects.create(
        user=user, base_case=case_to_exclude, type=Task.Type.REMINDER, date=date.today()
    )

    assert exclude_cases_with_pending_reminders(cases=[base_case, case_to_exclude]) == [
        base_case,
    ]
