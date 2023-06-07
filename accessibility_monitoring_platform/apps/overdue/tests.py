""" Tests for overdue app """

import pytest

from datetime import datetime, timedelta, date

from django.contrib.auth.models import User

from ..cases.models import (
    Case,
    TEST_STATUS_COMPLETE,
    ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
    WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
    REPORT_APPROVED_STATUS_APPROVED,
)
from ..cases.views import (
    calculate_report_followup_dates,
    calculate_twelve_week_chaser_dates,
)
from ..common.models import BOOLEAN_TRUE
from .utils import get_overdue_cases

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
    case: Case = Case.objects.create(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        test_results_url="https://www.test-results.com",
        test_status=TEST_STATUS_COMPLETE,
        accessibility_statement_state=ACCESSIBILITY_STATEMENT_DECISION_COMPLIANT,
        website_compliance_state_initial=WEBSITE_INITIAL_COMPLIANCE_COMPLIANT,
        report_draft_url="https://www.report-draft.com",
        report_review_status=BOOLEAN_TRUE,
        reviewer=user,
        report_approved_status=REPORT_APPROVED_STATUS_APPROVED,
        report_final_pdf_url="https://www.report-pdf.com",
        report_final_odt_url="https://www.report-odt.com",
    )
    return case


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
    assert case.in_report_correspondence_progress == "1-week followup due"


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
    assert case.in_report_correspondence_progress == "4-week followup due"


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
        == "4-week followup sent, case needs to progress"
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
    a one-week follow-up after the 12-week waiting period.
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
    assert case.twelve_week_correspondence_progress == "1-week followup due"


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
        == "1-week followup sent, case needs to progress"
    )
