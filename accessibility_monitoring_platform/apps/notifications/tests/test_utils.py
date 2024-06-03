""" Tests - test for notifications template tags """

from datetime import date, datetime, timedelta
from typing import List, Optional

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Retest
from ...cases.models import Case, CaseCompliance, EqualityBodyCorrespondence
from ...cases.utils import create_case_and_compliance
from ...cases.views import (
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
)
from ...common.models import Boolean
from ..models import Notification, NotificationSetting, Option, Task
from ..utils import add_task, get_overdue_cases, get_post_case_tasks, read_tasks

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
ONE_WEEK_AGO = TODAY - timedelta(days=8)
TWO_WEEKS_AGO = TODAY - timedelta(days=15)
THREE_WEEKS_AGO = TODAY - timedelta(days=22)
FOUR_WEEKS_AGO = TODAY - timedelta(days=29)
FIVE_WEEKS_AGO = TODAY - timedelta(days=36)
ELEVEN_WEEKS_AGO = TODAY - timedelta(days=85)
TWELVE_WEEKS_AGO = TODAY - timedelta(days=85)
THIRTEEN_WEEKS_AGO = TODAY - timedelta(days=92)
FOURTEEN_WEEKS_AGO = TODAY - timedelta(days=99)


def create_case(user: User) -> Case:
    case: Case = create_case_and_compliance(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_draft_url="https://www.report-draft.com",
        report_review_status=Boolean.YES,
        reviewer=user,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_final_pdf_url="https://www.report-pdf.com",
        report_final_odt_url="https://www.report-odt.com",
    )
    return case


@pytest.mark.django_db
def test_read_tasks_marks_task_as_read(rf):
    """test to check if read_tasks function marks tasks as read"""
    request: HttpRequest = rf.get("/")
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@mock.com", password="secret"
    )
    request.user = user
    case: Case = Case.objects.create()

    task: Task = Task.objects.create(
        date=date.today(), user=user, case=case, type=Task.Type.QA_COMMENT
    )

    assert not task.read

    read_tasks(user=user, case=case, type=Task.Type.QA_COMMENT)

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
    case: Case = Case.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

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
    case: Case = Case.objects.create()

    assert Task.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

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
    case: Case = Case.objects.create()

    assert Notification.objects.all().first() is None
    assert NotificationSetting.objects.all().first() is None

    add_task(
        user=user,
        case=case,
        type=type,
        description="this is a notification",
        list_description="There is a notification",
        request=request,
    )

    task: Optional[Task] = Task.objects.all().first()

    assert task is not None
    assert task.description == "this is a notification"
    assert len(mailoutbox) == 0

    notification_setting: Optional[NotificationSetting] = (
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

    case: Case = Case.objects.create(auditor=user)
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    post_case_tasks: List[Task] = get_post_case_tasks(user=user)

    assert len(post_case_tasks) == 1

    post_case_task: Task = post_case_tasks[0]

    assert post_case_task.type == Task.Type.POSTCASE
    assert post_case_task.date == equality_body_correspondence.created.date()
    assert post_case_task.case == case
    assert post_case_task.description == "Unresolved correspondence"
    assert len(post_case_task.options) == 1

    option: Option = post_case_task.options[0]

    assert (
        option.url
        == f"{equality_body_correspondence.get_absolute_url()}?view=unresolved"
    )
    assert option.label == "View correspondence"

    equality_body_correspondence.status = EqualityBodyCorrespondence.Status.RESOLVED
    equality_body_correspondence.save()

    assert len(get_post_case_tasks(user=user)) == 0

    retest: Retest = Retest.objects.create(case=case)

    post_case_tasks: List[Task] = get_post_case_tasks(user=user)

    assert len(post_case_tasks) == 1

    post_case_task: Task = post_case_tasks[0]

    assert post_case_task.type == Task.Type.POSTCASE
    assert post_case_task.date == retest.date_of_retest
    assert post_case_task.case == case
    assert post_case_task.description == "Incomplete retest"

    option: Option = post_case_task.options[0]

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

    case: Case = create_case(user)

    assert len(get_overdue_cases(user)) == 0

    case.contact_details_found = Case.ContactDetailsFound.NOT_FOUND
    case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case.save()

    assert len(get_overdue_cases(user)) == 1


@pytest.mark.django_db
def test_returns_no_overdue_cases():
    """Creates seven cases that are all in correspondence with the PSB but require no further actions.
    Should return an empty queryset as none are overdue.
    """
    user: User = User.objects.create()

    # Case #1 - ready to be sent
    case: Case = create_case(user)

    # Case #2 - Sent, waiting for one week followup
    case: Case = create_case(user)
    case.report_sent_date = TODAY
    case.save()

    # Case #3 - Sent one week followup, waiting for four week followup
    case: Case = create_case(user)
    case.report_sent_date = ONE_WEEK_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_followup_week_1_sent_date = YESTERDAY
    case.save()

    # Case #4 - Sent four week followup, waiting for five day deadline
    case: Case = create_case(user)
    case.report_sent_date = FOUR_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    case.report_followup_week_4_sent_date = YESTERDAY
    case.save()

    # Case #5 - Report has been acknolwedged, waiting for 12-week deadline
    case: Case = create_case(user)
    case.report_sent_date = FOUR_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    case.report_followup_week_4_sent_date = YESTERDAY
    case.report_acknowledged_date = datetime.now()
    case.save()

    # Case #6 - Case is past 12-week deadline, update requested
    case: Case = create_case(user)
    case.report_sent_date = TWELVE_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_acknowledged_date = ELEVEN_WEEKS_AGO
    case.twelve_week_update_requested_date = TODAY
    case.save()

    # Case #7 - Case is past 1 week deadline for update, 1 week chaser requested
    case: Case = create_case(user)
    case.report_sent_date = THIRTEEN_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_acknowledged_date = TWELVE_WEEKS_AGO
    case.twelve_week_update_requested_date = ONE_WEEK_AGO
    case.twelve_week_1_week_chaser_sent_date = TODAY
    case.save()

    assert list(get_overdue_cases(user)) == []


@pytest.mark.django_db
def test_in_report_correspondence_week_1_overdue():
    """Creates two cases; one that is not overdue and another that requires a one-week chaser."""
    user: User = User.objects.create()
    new_case: Case = create_case(user)
    new_case.report_sent_date = datetime.now()
    new_case.save()

    case: Case = create_case(user)

    case.report_sent_date = ONE_WEEK_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert case.in_report_correspondence_progress == "1-week follow-up to report due"


@pytest.mark.django_db
def test_in_report_correspondence_week_4_overdue():
    """Creates two cases; one that is not overdue and another that requires a four-week chaser."""
    user: User = User.objects.create()
    create_case(user)

    case: Case = create_case(user)
    case.report_sent_date = FOUR_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_followup_week_1_sent_date = THREE_WEEKS_AGO
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert case.in_report_correspondence_progress == "4-week follow-up to report due"


@pytest.mark.django_db
def test_in_report_correspondence_psb_overdue_after_four_week_reminder():
    """Creates two cases; one that is not overdue and another that needs to be moved to equality body correspondence."""
    user: User = User.objects.create()
    create_case(user)

    case: Case = create_case(user)
    case.report_sent_date = FIVE_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_followup_week_1_sent_date = FOUR_WEEKS_AGO
    case.report_followup_week_4_sent_date = ONE_WEEK_AGO
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        case.in_report_correspondence_progress
        == "4-week follow-up to report sent, case needs to progress"
    )


@pytest.mark.django_db
def test_in_probation_period_overdue():
    """Creates two cases; one that is not overdue and another that needs to be moved to equality body correspondence."""
    user: User = User.objects.create()
    create_case(user)

    case: Case = create_case(user)
    case.report_sent_date = THIRTEEN_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_acknowledged_date = TWELVE_WEEKS_AGO
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1


@pytest.mark.django_db
def test_in_12_week_correspondence_1_week_followup_overdue():
    """
    Creates two cases; one that is not overdue and another that needs
    a one-week followup after the 12-week waiting period.
    """
    user: User = User.objects.create()
    create_case(user)

    case: Case = create_case(user)
    case.report_sent_date = THIRTEEN_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_acknowledged_date = THIRTEEN_WEEKS_AGO
    case.twelve_week_update_requested_date = ONE_WEEK_AGO
    case = calculate_twelve_week_chaser_dates(
        case, case.twelve_week_update_requested_date
    )
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert case.twelve_week_correspondence_progress == "1-week follow-up due"


@pytest.mark.django_db
def test_in_12_week_correspondence_psb_overdue_after_one_week_reminder():
    """
    Creates two cases; one that is not overdue and another that needs
    to move to final decision after the 12-week waiting period.
    """
    user: User = User.objects.create()
    create_case(user)

    case: Case = create_case(user)
    case.report_sent_date = FOURTEEN_WEEKS_AGO
    case = calculate_report_followup_dates(case, case.report_sent_date)
    case.report_acknowledged_date = FOURTEEN_WEEKS_AGO
    case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    case = calculate_twelve_week_chaser_dates(
        case, case.twelve_week_update_requested_date
    )
    case.twelve_week_1_week_chaser_sent_date = ONE_WEEK_AGO
    case.save()

    assert len(Case.objects.all()) == 2
    assert len(get_overdue_cases(user)) == 1
    assert (
        case.twelve_week_correspondence_progress
        == "1-week follow-up sent, case needs to progress"
    )
