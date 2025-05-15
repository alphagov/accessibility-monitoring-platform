"""
Tests for cases models
"""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.urls import reverse
from pytest_django.asserts import assertQuerySetEqual

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    Retest,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)
from ...comments.models import Comment
from ...common.models import Boolean, EmailTemplate
from ...notifications.models import Task
from ...reports.models import Report, ReportVisitsMetrics
from ...s3_read_write.models import S3Report
from ..models import (
    Case,
    CaseCompliance,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
    EventHistory,
    ZendeskTicket,
)
from ..utils import create_case_and_compliance

DOMAIN: str = "example.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}/index.html"
ORGANISATION_NAME: str = "Organisation name"
DATETIME_HISTORIC: datetime = datetime(2020, 9, 15, tzinfo=timezone.utc)
DATETIME_CASE_CREATED: datetime = datetime(2021, 9, 15, tzinfo=timezone.utc)
DATETIME_CASE_UPDATED: datetime = datetime(2021, 9, 16, tzinfo=timezone.utc)
DATETIME_CONTACT_CREATED: datetime = datetime(2021, 9, 17, tzinfo=timezone.utc)
DATETIME_CONTACT_UPDATED: datetime = datetime(2021, 9, 18, tzinfo=timezone.utc)
DATE_AUDIT_CREATED: date = date(2021, 9, 19)
DATETIME_AUDIT_CREATED: datetime = datetime(2021, 9, 19, tzinfo=timezone.utc)
DATETIME_AUDIT_UPDATED: datetime = datetime(2021, 9, 20, tzinfo=timezone.utc)
DATETIME_PAGE_CREATED: datetime = datetime(2021, 9, 21, tzinfo=timezone.utc)
DATETIME_PAGE_UPDATED: datetime = datetime(2021, 9, 22, tzinfo=timezone.utc)
DATETIME_CHECK_RESULT_CREATED: datetime = datetime(2021, 9, 23, tzinfo=timezone.utc)
DATETIME_CHECK_RESULT_UPDATED: datetime = datetime(2021, 9, 24, tzinfo=timezone.utc)
DATETIME_COMMENT_CREATED: datetime = datetime(2021, 9, 25, tzinfo=timezone.utc)
DATETIME_COMMENT_UPDATED: datetime = datetime(2021, 9, 26, tzinfo=timezone.utc)
REMINDER_DUE_DATE: date = date(2022, 1, 1)
DATETIME_REMINDER_UPDATED: datetime = datetime(2021, 9, 27, tzinfo=timezone.utc)
DATETIME_REPORT_UPDATED: datetime = datetime(2021, 9, 28, tzinfo=timezone.utc)
DATETIME_S3REPORT_UPDATED: datetime = datetime(2021, 9, 29, tzinfo=timezone.utc)
NO_CONTACT_DATE: date = date(2020, 4, 1)
NO_CONTACT_ONE_WEEK: date = NO_CONTACT_DATE + timedelta(days=7)
NO_CONTACT_FOUR_WEEKS: date = NO_CONTACT_DATE + timedelta(days=28)
TODAY: date = date.today()
ONE_WEEK_AGO = TODAY - timedelta(days=7)
TWO_WEEKS_AGO = TODAY - timedelta(days=14)
FOUR_WEEKS_AGO = TODAY - timedelta(days=28)


def create_case_for_overdue_link() -> Case:
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        reviewer=user,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )
    return case


@pytest.fixture
def last_edited_case() -> Case:
    """Pytest fixture case for testing last edited timestamp values"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_CASE_CREATED)):
        return Case.objects.create()


@pytest.fixture
def last_edited_audit(last_edited_case: Case) -> Audit:
    """Pytest fixture audit for testing last edited timestamp values"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_CREATED)):
        return Audit.objects.create(
            case=last_edited_case, date_of_test=DATE_AUDIT_CREATED
        )


@pytest.mark.django_db
def test_case_number_incremented_on_creation():
    """Test that each new case gets the next case_number"""
    case_one: Case = Case.objects.create()

    assert case_one.case_number == 1

    case_two: Case = Case.objects.create()

    assert case_two.case_number == 2


@pytest.mark.django_db
def test_case_creation_also_creates_compliance():
    """Test that creating a case also creates a CaseCompliance"""
    case: Case = Case.objects.create()

    assert case.compliance is not None
    assert case.compliance.website_compliance_state_initial is not None
    assert case.compliance.website_compliance_notes_initial is not None
    assert case.compliance.statement_compliance_state_initial is not None
    assert case.compliance.statement_compliance_notes_initial is not None
    assert case.compliance.website_compliance_state_12_week is not None
    assert case.compliance.website_compliance_notes_12_week is not None
    assert case.compliance.statement_compliance_state_12_week is not None
    assert case.compliance.statement_compliance_notes_12_week is not None


@pytest.mark.django_db
def test_case_created_timestamp_is_populated():
    """Test the Case created field is populated the first time the Case is saved"""
    case: Case = Case.objects.create()

    assert case.created is not None
    assert isinstance(case.created, datetime)


@pytest.mark.django_db
def test_case_created_timestamp_is_not_updated():
    """Test the Case created field is not updated on subsequent saves"""
    case: Case = Case.objects.create()

    original_created_timestamp: datetime = case.created
    updated_organisation_name: str = "updated organisation name"
    case.organisation_name = updated_organisation_name
    case.save()
    updated_case: Case = Case.objects.get(pk=case.id)

    assert updated_case.organisation_name == updated_organisation_name
    assert updated_case.created == original_created_timestamp


@pytest.mark.django_db
def test_case_domain_is_populated_from_home_page_url():
    """Test the Case domain field is populated from the home_page_url"""
    case: Case = Case.objects.create(home_page_url=HOME_PAGE_URL)

    assert case.domain == DOMAIN


@pytest.mark.django_db
def test_case_renders_as_organisation_name_bar_id():
    """Test the Case string is organisation_name | id"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)

    assert str(case) == f"{case.organisation_name} | #{case.case_number}"


@pytest.mark.django_db
def test_case_title_is_organisation_name_bar_id():
    """Test the Case title string is organisation_name | id"""
    case: Case = Case.objects.create(
        home_page_url=HOME_PAGE_URL, organisation_name=ORGANISATION_NAME
    )

    assert case.title == f"{case.organisation_name} &nbsp;|&nbsp; #{case.case_number}"


@pytest.mark.django_db
def test_case_completed_timestamp_is_updated_on_completion():
    """Test the Case completed date field is updated when case_completed is set"""
    case: Case = Case.objects.create()

    assert case.completed_date is None

    case.case_completed = "no-action"
    case.save()
    updated_case: Case = Case.objects.get(pk=case.id)

    assert updated_case.completed_date is not None
    assert isinstance(updated_case.completed_date, datetime)


@pytest.mark.django_db
def test_contact_created_timestamp_is_populated():
    """Test the created field is populated the first time the Contact is saved"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    assert contact.created is not None
    assert isinstance(contact.created, datetime)


@pytest.mark.django_db
def test_contact_created_timestamp_is_not_updated():
    """Test the created field is not updated on subsequent save"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    original_created_timestamp: datetime = contact.created
    updated_name: str = "updated name"
    contact.name = updated_name
    contact.save()
    updated_contact: Contact = Contact.objects.get(pk=contact.id)

    assert updated_contact.name == updated_name
    assert updated_contact.created == original_created_timestamp


@pytest.mark.django_db
def test_most_recently_created_contact_returned_first():
    """Test the contacts are returned in most recently created order"""
    case: Case = Case.objects.create()
    contact1: Contact = Contact.objects.create(case=case)
    contact2: Contact = Contact.objects.create(case=case)

    contacts: list[Contact] = list(case.contacts)

    assert contacts[0].id == contact2.id
    assert contacts[1].id == contact1.id


@pytest.mark.django_db
def test_deleted_contacts_not_returned():
    """Test that deleted contacts are not returned"""
    case: Case = Case.objects.create()
    contact1: Contact = Contact.objects.create(case=case)
    contact2: Contact = Contact.objects.create(case=case)

    contacts: list[Contact] = list(case.contacts)

    assert len(contacts) == 2

    contact1.is_deleted = True
    contact1.save()

    contacts: list[Contact] = list(case.contacts)

    assert len(contacts) == 1
    assert contacts[0].id == contact2.id


@pytest.mark.django_db
def test_preferred_contact_returned_first():
    """
    Test the contacts are returned in most recently created order with preferred contact first
    """
    case: Case = Case.objects.create()
    preferred_contact: Contact = Contact.objects.create(case=case, preferred="yes")
    contact1: Contact = Contact.objects.create(case=case)
    contact2: Contact = Contact.objects.create(case=case)

    contacts: list[Contact] = list(case.contacts)

    assert contacts[0].id == preferred_contact.id
    assert contacts[1].id == contact2.id
    assert contacts[2].id == contact1.id


@pytest.mark.django_db
def test_contact_exists():
    """Test the contacts exists"""
    case: Case = Case.objects.create()

    assert case.contact_exists is False

    Contact.objects.create(case=case)

    assert case.contact_exists is True


@pytest.mark.parametrize(
    "compliance_email_sent_date, expected_psb_appeal_deadline",
    [
        (None, None),
        (date(2020, 1, 1), date(2020, 1, 29)),
    ],
)
def test_psb_appeal_deadline(compliance_email_sent_date, expected_psb_appeal_deadline):
    case: Case = Case(compliance_email_sent_date=compliance_email_sent_date)

    assert case.psb_appeal_deadline == expected_psb_appeal_deadline


@pytest.mark.parametrize(
    "url, expected_formatted_url",
    [
        ("https://gov.uk/bank-holidays/", "gov.uk/bank-holidays"),
        ("https://www.google.com/maps", "google.com/maps"),
        (
            "http://www.google.com/search?q=bbc+news&oq=&aqs=chrome.3.69i5"
            "9i450l8.515265j0j7&sourceid=chrome&ie=UTF-8",
            "google.com/search?q=bbc+n…",
        ),
        ("https://www3.halton.gov.uk/Pages/Home.aspx", "halton.gov.uk/Pages/Home.…"),
    ],
)
def test_formatted_home_page_url(url, expected_formatted_url):
    case: Case = Case(home_page_url=url)
    assert case.formatted_home_page_url == expected_formatted_url


@pytest.mark.django_db
def test_next_action_due_date_for_report_ready_to_send():
    """
    Check that the next_action_due_date is correctly returned
    when case status is report ready to send.
    """
    seven_day_no_contact_email_sent_date: date = NO_CONTACT_DATE
    no_contact_one_week_chaser_due_date: date = NO_CONTACT_ONE_WEEK
    no_contact_four_week_chaser_due_date: date = NO_CONTACT_FOUR_WEEKS

    case: Case = Case.objects.create(
        seven_day_no_contact_email_sent_date=seven_day_no_contact_email_sent_date,
        no_contact_one_week_chaser_due_date=no_contact_one_week_chaser_due_date,
        no_contact_four_week_chaser_due_date=no_contact_four_week_chaser_due_date,
    )
    case.status.status = "report-ready-to-send"

    # Initial no countact details request sent
    assert case.next_action_due_date == no_contact_one_week_chaser_due_date

    case.no_contact_one_week_chaser_sent_date = NO_CONTACT_ONE_WEEK

    # No contact details 1-week chaser sent
    assert case.next_action_due_date == no_contact_four_week_chaser_due_date

    case.no_contact_four_week_chaser_sent_date = NO_CONTACT_FOUR_WEEKS

    # No contact details 4-week chaser sent
    assert case.next_action_due_date == NO_CONTACT_FOUR_WEEKS + timedelta(days=7)


@pytest.mark.django_db
def test_next_action_due_date_for_in_report_correspondence():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in report correspondence.
    """
    any_old_date: date = date(2020, 4, 1)
    report_followup_week_1_due_date: date = date(2020, 1, 1)
    report_followup_week_4_due_date: date = date(2020, 1, 4)
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case.objects.create(
        report_followup_week_1_sent_date=any_old_date,
        report_followup_week_4_sent_date=any_old_date,
        report_followup_week_1_due_date=report_followup_week_1_due_date,
        report_followup_week_4_due_date=report_followup_week_4_due_date,
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )
    case.status.status = "in-report-correspondence"

    case.report_followup_week_4_sent_date = None
    assert case.next_action_due_date == report_followup_week_4_due_date

    case.report_followup_week_1_sent_date = None
    assert case.next_action_due_date == report_followup_week_1_due_date


@pytest.mark.django_db
def test_next_action_due_date_for_in_probation_period():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in probation period.
    """
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )
    case.status.status = "in-probation-period"

    assert case.next_action_due_date == report_followup_week_12_due_date


@pytest.mark.django_db
def test_next_action_due_date_for_in_12_week_correspondence():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in 12-week correspondence.
    """
    twelve_week_1_week_chaser_due_date: date = date(2020, 1, 1)

    case: Case = Case.objects.create(
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
    )
    case.status.status = "in-12-week-correspondence"

    assert case.next_action_due_date == twelve_week_1_week_chaser_due_date

    twelve_week_1_week_chaser_sent_date: date = date(2020, 1, 1)
    case.twelve_week_1_week_chaser_sent_date = twelve_week_1_week_chaser_sent_date

    assert case.next_action_due_date == twelve_week_1_week_chaser_sent_date + timedelta(
        days=7
    )


@pytest.mark.parametrize(
    "status",
    [
        "unknown",
        "unassigned-case",
        "test-in-progress",
        "report-in-progress",
        "unassigned-qa-case",
        "qa-in-progress",
        "report-ready-to-send",
        "final-decision-due",
        "in-correspondence-with-equalities-body",
        "complete",
    ],
)
@pytest.mark.django_db
def test_next_action_due_date_not_set(status):
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in probation period.
    """
    twelve_week_1_week_chaser_due_date: date = date(2020, 1, 1)
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
    )
    case.status.status = status

    assert case.next_action_due_date == date(1970, 1, 1)


@pytest.mark.parametrize(
    "report_followup_week_12_due_date, expected_tense",
    [
        (TODAY - timedelta(days=1), "past"),
        (TODAY, "present"),
        (TODAY + timedelta(days=1), "future"),
    ],
)
@pytest.mark.django_db
def test_next_action_due_date_tense(report_followup_week_12_due_date, expected_tense):
    """Check that the calculated next_action_due_date is correctly reported"""
    case: Case = Case.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )
    case.status.status = "in-probation-period"

    assert case.next_action_due_date_tense == expected_tense


@pytest.mark.django_db
def test_case_save_increments_version():
    """Test that saving a Case increments its version"""
    case: Case = Case.objects.create()
    old_version: int = case.version
    case.save()

    assert case.version == old_version + 1


@pytest.mark.django_db
def test_qa_comments():
    """
    Test the QA comments are returned in most recently created order
    """
    case: Case = Case.objects.create()
    Comment.objects.create(case=case, hidden=True)
    comment1: Comment = Comment.objects.create(case=case)
    comment2: Comment = Comment.objects.create(case=case)

    comments: list[Contact] = case.qa_comments

    assert len(comments) == 2
    assert comments[0].id == comment2.id
    assert comments[1].id == comment1.id


@pytest.mark.django_db
def test_qa_comments_count():
    """Test the QA comments count"""
    case: Case = Case.objects.create()
    Comment.objects.create(case=case, hidden=True)
    Comment.objects.create(case=case)
    Comment.objects.create(case=case)

    assert case.qa_comments_count == 2


@pytest.mark.parametrize(
    "previous_case_url, previous_case_number",
    [
        ("https://...gov.uk/cases/191/view/", "191"),
        ("", None),
        ("https://...gov.uk/audits/191/view/", None),
    ],
)
def test_previous_case_number(previous_case_url, previous_case_number):
    """Test previous case number derived from url"""
    case: Case = Case(previous_case_url=previous_case_url)

    assert case.previous_case_number == previous_case_number


@pytest.mark.django_db
def test_case_last_edited_from_case(last_edited_case: Case):
    """Test the case last edited date found on Case"""
    assert last_edited_case.last_edited == DATETIME_CASE_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_CASE_UPDATED)):
        last_edited_case.save()

    assert last_edited_case.last_edited == DATETIME_CASE_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_contact(last_edited_case: Case):
    """Test the case last edited date found on Contact"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CONTACT_CREATED)
    ):
        contact: Contact = Contact.objects.create(case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_CONTACT_CREATED

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CONTACT_UPDATED)
    ):
        contact.save()

    assert last_edited_case.last_edited == DATETIME_CONTACT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_audit(last_edited_case: Case, last_edited_audit: Audit):
    """Test the case last edited date found on Audit"""
    assert last_edited_case.last_edited == DATETIME_AUDIT_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_UPDATED)):
        last_edited_audit.save()

    assert last_edited_case.last_edited == DATETIME_AUDIT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_page(last_edited_case: Case, last_edited_audit: Audit):
    """Test the case last edited date found on Page"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_CREATED)):
        page: Page = Page.objects.create(audit=last_edited_audit)

    assert last_edited_case.last_edited == DATETIME_PAGE_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        page.save()

    assert last_edited_case.last_edited == DATETIME_PAGE_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_check_result(
    last_edited_case: Case, last_edited_audit: Audit
):
    """Test the case last edited date found on CheckResult"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_CREATED)):
        page: Page = Page.objects.create(audit=last_edited_audit)

    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_CREATED)
    ):
        check_result: CheckResult = CheckResult.objects.create(
            audit=last_edited_audit,
            page=page,
            type=WcagDefinition.Type.AXE,
            wcag_definition=wcag_definition,
        )

    assert last_edited_case.last_edited == DATETIME_CHECK_RESULT_CREATED

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_UPDATED)
    ):
        check_result.save()

    assert last_edited_case.last_edited == DATETIME_CHECK_RESULT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_comment(last_edited_case: Case):
    """Test the case last edited date found on Comment"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_CREATED)
    ):
        comment: Comment = Comment.objects.create(case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_COMMENT_CREATED

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_UPDATED)
    ):
        comment.save()

    assert last_edited_case.last_edited == DATETIME_COMMENT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_reminder(last_edited_case: Case):
    """Test the case last edited date found on reminder Task"""
    user: User = User.objects.create()
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_REMINDER_UPDATED)
    ):
        Task.objects.create(
            type=Task.Type.REMINDER,
            case=last_edited_case,
            user=user,
            date=REMINDER_DUE_DATE,
        )

    assert last_edited_case.last_edited == DATETIME_REMINDER_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_report(last_edited_case: Case):
    """Test the case last edited date found on Report"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_REPORT_UPDATED)):
        Report.objects.create(case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_REPORT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_s3_report(last_edited_case: Case):
    """Test the case last edited date found on S3Report"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_S3REPORT_UPDATED)
    ):
        S3Report.objects.create(case=last_edited_case, version=0)

    assert last_edited_case.last_edited == DATETIME_S3REPORT_UPDATED


@pytest.mark.django_db
def test_case_statement_checks_still_initial():
    """
    Test statement state has not been determined. Either because the statement
    state is still the default or, if statement checks exist, one of the
    overview checks is still not tested.
    """
    case: Case = Case.objects.create()

    assert case.statement_checks_still_initial is True

    case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )

    assert case.statement_checks_still_initial is False

    audit: Audit = Audit.objects.create(case=case)
    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    assert case.statement_checks_still_initial is True

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert case.statement_checks_still_initial is False


@pytest.mark.django_db
def test_contact_updated_updated():
    """Test the contact updated field is updated"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(case=case)

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CONTACT_UPDATED)
    ):
        contact.save()

    assert contact.updated == DATETIME_CONTACT_UPDATED


@pytest.mark.parametrize(
    "website_compliance_state_initial, website_compliance_state_12_week, expected_result",
    [
        (
            CaseCompliance.WebsiteCompliance.UNKNOWN,
            CaseCompliance.WebsiteCompliance.UNKNOWN,
            "Not known",
        ),
        (CaseCompliance.WebsiteCompliance.UNKNOWN, "compliant", "Fully compliant"),
        (
            CaseCompliance.WebsiteCompliance.UNKNOWN,
            "partially-compliant",
            "Partially compliant",
        ),
        (
            CaseCompliance.WebsiteCompliance.COMPLIANT,
            CaseCompliance.WebsiteCompliance.UNKNOWN,
            "Fully compliant",
        ),
        (
            "partially-compliant",
            CaseCompliance.WebsiteCompliance.UNKNOWN,
            "Partially compliant",
        ),
    ],
)
@pytest.mark.django_db
def test_website_compliance_display(
    website_compliance_state_initial, website_compliance_state_12_week, expected_result
):
    """Test website compliance is derived correctly"""
    case: Case = create_case_and_compliance(
        website_compliance_state_initial=website_compliance_state_initial,
        website_compliance_state_12_week=website_compliance_state_12_week,
    )

    assert case.website_compliance_display == expected_result


@pytest.mark.django_db
def test_percentage_website_issues_fixed_no_audit():
    """Test that cases without audits return n/a"""
    case: Case = Case.objects.create()

    assert case.percentage_website_issues_fixed == "n/a"


@pytest.mark.django_db
def test_overview_issues_website_with_audit_no_issues():
    """Test that case with audit but no issues returns n/a"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)

    assert case.percentage_website_issues_fixed == "n/a"


@pytest.mark.django_db
def test_percentage_website_issues_fixed_with_audit_and_issues():
    """Test that case with audit and issues returns percentage"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=WcagDefinition.Type.AXE,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )

    assert case.percentage_website_issues_fixed == 0

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    assert case.percentage_website_issues_fixed == 100


@pytest.mark.django_db
def test_overview_issues_website_no_audit():
    """Test that cases without audits return no test exists"""
    case: Case = Case.objects.create()

    assert case.overview_issues_website == "No test exists"


@pytest.mark.django_db
def test_overview_issues_statement_no_audit():
    """Test that cases without audits return no test exists"""
    case: Case = Case.objects.create()

    assert case.overview_issues_statement == "No test exists"


@pytest.mark.django_db
def test_overview_issues_website_with_audit():
    """Test that case with audit returns overview"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert case.overview_issues_website == "0 of 0 fixed"

    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=WcagDefinition.Type.AXE,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )

    assert case.overview_issues_website == "0 of 1 fixed (0%)"

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    assert case.overview_issues_website == "1 of 1 fixed (100%)"


@pytest.mark.django_db
def test_overview_issues_statement_with_statement_checks():
    """Test that case with audit returns overview"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for count, statement_check in enumerate(StatementCheck.objects.all()):
        check_result_state: str = (
            StatementCheckResult.Result.NO
            if count % 2 == 0
            else StatementCheckResult.Result.YES
        )
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=check_result_state,
        )

    assert case.overview_issues_statement == "21 checks failed on test"

    for count, statement_check_result in enumerate(
        audit.failed_statement_check_results
    ):
        if count % 2 == 0:
            statement_check_result.check_result_state = StatementCheckResult.Result.YES
            statement_check_result.save()

    assert case.overview_issues_statement == "10 checks failed on test"


def test_archived_sections():
    """Test archived sections"""
    case: Case = Case()

    assert case.archived_sections is None

    case.archive = json.dumps({"sections": ["section_one"]})

    assert len(case.archived_sections) == 1
    assert case.archived_sections[0] == "section_one"


@pytest.mark.django_db
def test_equality_body_correspondence_sets_id_within_case():
    """Test EqualityBodyCorrespondence sets id_within_case on save"""
    case: Case = Case.objects.create()

    first_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    assert first_equality_body_correspondence.id_within_case == 1

    second_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    assert second_equality_body_correspondence.id_within_case == 2


@pytest.mark.django_db
def test_case_retests_returns_undeleted_retests():
    """Test Case.retests returns undeleted retests"""
    case: Case = Case.objects.create()
    retest: Retest = Retest.objects.create(case=case)

    assert len(case.retests) == 1
    assert case.retests[0] == retest

    retest.is_deleted = True
    retest.save()

    assert len(case.retests) == 0


@pytest.mark.django_db
def test_case_number_retests():
    """
    Test Case.number_retests returns number of retests not counting
    Retest #0.
    """
    case: Case = Case.objects.create()
    Retest.objects.create(case=case)

    assert case.number_retests == 1

    Retest.objects.create(case=case, id_within_case=0)

    assert case.number_retests == 1


@pytest.mark.django_db
def test_case_latest_retest_returns_most_recent():
    """Test Case.latest_retest returns most recent"""
    case: Case = Case.objects.create()

    assert case.latest_retest is None

    first_retest: Retest = Retest.objects.create(case=case)

    assert case.latest_retest == first_retest

    second_retest: Retest = Retest.objects.create(case=case, id_within_case=2)

    assert case.latest_retest == second_retest


@pytest.mark.django_db
def test_case_incomplete_retests_returns_incomplete_retests():
    """Test Case.incomplete_retests returns retests with the default state"""
    case: Case = Case.objects.create()
    incomplete_retest: Retest = Retest.objects.create(case=case)

    assert len(case.incomplete_retests) == 1
    assert case.incomplete_retests[0] == incomplete_retest

    incomplete_retest.retest_compliance_state = Retest.Compliance.COMPLIANT
    incomplete_retest.save()

    assert len(case.incomplete_retests) == 0


@pytest.mark.django_db
def test_case_equality_body_correspondences_returns_undeleted_equality_body_correspondences():
    """Test Case.equality_body_correspondences returns undeleted equality_body_correspondences"""
    case: Case = Case.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    assert len(case.equality_body_correspondences) == 1
    assert case.equality_body_correspondences[0] == equality_body_correspondence

    equality_body_correspondence.is_deleted = True
    equality_body_correspondence.save()

    assert len(case.equality_body_questions) == 0


@pytest.mark.django_db
def test_equality_body_correspondences_unresolved_count():
    """
    Test Case.equality_body_correspondences_unresolved_count returns number of
    unresolved equality_body_correspondences.
    """
    case: Case = Case.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(case=case)
    )

    assert case.equality_body_correspondences_unresolved_count == 1

    equality_body_correspondence.status = EqualityBodyCorrespondence.Status.RESOLVED
    equality_body_correspondence.save()

    assert case.equality_body_correspondences_unresolved_count == 0


@pytest.mark.django_db
def test_case_equality_body_questions_returns_equality_body_questions():
    """Test Case.equality_body_questions returns equality_body_questions"""
    case: Case = Case.objects.create()
    equality_body_question: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EqualityBodyCorrespondence.Type.QUESTION
        )
    )

    assert len(case.equality_body_questions) == 1
    assert case.equality_body_questions[0] == equality_body_question


@pytest.mark.django_db
def test_case_equality_body_questions_unresolved_returns_unresolved():
    """Test Case.equality_body_questions_unresolved returns questions with the default state"""
    case: Case = Case.objects.create()
    unresolved_question: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EqualityBodyCorrespondence.Type.QUESTION
        )
    )

    assert len(case.equality_body_questions_unresolved) == 1
    assert case.equality_body_questions_unresolved[0] == unresolved_question

    unresolved_question.status = EqualityBodyCorrespondence.Status.RESOLVED
    unresolved_question.save()

    assert len(case.equality_body_questions_unresolved) == 0


@pytest.mark.django_db
def test_case_equality_body_correspondence_retests_returns_equality_body_correspondence_retests():
    """Test Case.equality_body_correspondence_retests returns equality_body_correspondence_retests"""
    case: Case = Case.objects.create()
    equality_body_retest: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EqualityBodyCorrespondence.Type.RETEST
        )
    )

    assert len(case.equality_body_correspondence_retests) == 1
    assert case.equality_body_correspondence_retests[0] == equality_body_retest


@pytest.mark.django_db
def test_case_equality_body_correspondence_retests_unresolved_returns_unresolved():
    """Test Case.equality_body_correspondence_retests_unresolved returns retests with the default state"""
    case: Case = Case.objects.create()
    unresolved_retest: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EqualityBodyCorrespondence.Type.RETEST
        )
    )

    assert len(case.equality_body_correspondence_retests_unresolved) == 1
    assert case.equality_body_correspondence_retests_unresolved[0] == unresolved_retest

    unresolved_retest.status = EqualityBodyCorrespondence.Status.RESOLVED
    unresolved_retest.save()

    assert len(case.equality_body_correspondence_retests_unresolved) == 0


@pytest.mark.django_db
def test_calulate_qa_status_unassigned():
    """Test Case calulate_qa_status correctly returns unassigned"""
    case: Case = Case.objects.create(report_review_status=Boolean.YES)

    assert case.calulate_qa_status() == Case.QAStatus.UNASSIGNED


@pytest.mark.django_db
def test_calulate_qa_status_in_qa():
    """Test Case calulate_qa_status correctly returns In-QA"""
    user: User = User.objects.create()
    case: Case = Case.objects.create(
        reviewer=user,
        report_review_status=Boolean.YES,
    )

    assert case.calulate_qa_status() == Case.QAStatus.IN_QA


@pytest.mark.django_db
def test_calulate_qa_status_approved():
    """Test Case calulate_qa_status correctly returns approved"""
    case: Case = Case.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
    )

    assert case.calulate_qa_status() == Case.QAStatus.APPROVED


@pytest.mark.django_db
def test_total_website_issues():
    """Test Case total_website_issues returns number found or n/a if none"""
    case: Case = Case.objects.create()

    assert case.total_website_issues == 0

    audit: Audit = Audit.objects.create(case=case)

    assert case.total_website_issues == 0

    home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert case.total_website_issues == 2


@pytest.mark.django_db
def test_total_website_issues_fixed():
    """Test Case total_website_issues_fixed returns number found or n/a if none"""
    case: Case = Case.objects.create()

    assert case.total_website_issues_fixed == 0

    audit: Audit = Audit.objects.create(case=case)

    assert case.total_website_issues_fixed == 0

    home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert case.total_website_issues_fixed == 1


@pytest.mark.django_db
def test_total_website_issues_unfixed():
    """Test Case total_website_issues_unfixed returns number found or n/a if none"""
    case: Case = Case.objects.create()

    assert case.total_website_issues_unfixed == 0

    audit: Audit = Audit.objects.create(case=case)

    assert case.total_website_issues_unfixed == 0

    home_page: Page = Page.objects.create(audit=audit, page_type=Page.Type.HOME)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create()
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    CheckResult.objects.create(
        audit=audit,
        page=home_page,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert case.total_website_issues_unfixed == 1


@pytest.mark.django_db
def test_csv_export_statement_initially_found():
    """Test Case csv_export_statement_initially_found"""
    case: Case = Case.objects.create()

    assert case.csv_export_statement_initially_found == "unknown"

    audit: Audit = Audit.objects.create(case=case)

    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=StatementCheckResult.Result.NO,
        )

    assert case.csv_export_statement_initially_found == "No"

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert case.csv_export_statement_initially_found == "Yes"


@pytest.mark.django_db
def test_csv_export_statement_found_at_12_week_retest():
    """Test Case csv_export_statement_found_at_12_week_retest"""
    case: Case = Case.objects.create()

    assert case.csv_export_statement_found_at_12_week_retest == "unknown"

    audit: Audit = Audit.objects.create(case=case)

    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            retest_state=StatementCheckResult.Result.NO,
        )

    assert case.csv_export_statement_found_at_12_week_retest == "No"

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.retest_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert case.csv_export_statement_found_at_12_week_retest == "Yes"


@pytest.mark.django_db
def test_case_latest_psb_zendesk_url():
    """Test Case.latest_psb_zendesk_url"""
    case: Case = Case.objects.create()

    assert case.latest_psb_zendesk_url == ""

    case.zendesk_url = "first"
    case.save()

    assert case.latest_psb_zendesk_url == "first"

    ZendeskTicket.objects.create(case=case, url="second")

    assert case.latest_psb_zendesk_url == "second"


@pytest.mark.django_db
def test_case_zendesk_tickets():
    """Test Case.zendesk_tickets"""
    case: Case = Case.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    assert case.zendesk_tickets.count() == 1
    assert case.zendesk_tickets.first() == zendesk_ticket

    zendesk_ticket.is_deleted = True
    zendesk_ticket.save()

    assert case.zendesk_tickets.count() == 0


@pytest.mark.django_db
def test_zendesk_ticket_get_absolute_url():
    """Test ZendeskTickets.get_absolute_url"""
    case: Case = Case.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    assert zendesk_ticket.get_absolute_url() == "/cases/1/update-zendesk-ticket/"


@pytest.mark.django_db
def test_zendesk_ticket_id_within_case():
    """Test ZendeskTicket.id_within_case"""
    case: Case = Case.objects.create()
    first_zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    assert first_zendesk_ticket.id_within_case == 1

    second_zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(case=case)

    assert second_zendesk_ticket.id_within_case == 2


@pytest.mark.django_db
def test_case_email_tmplates():
    """Test Case.email_templates returns expected data"""
    email_templates: QuerySet[EmailTemplate] = EmailTemplate.objects.filter(
        is_deleted=False
    )

    assert email_templates.count() == 4
    assertQuerySetEqual(Case().email_templates, email_templates)


@pytest.mark.django_db
def test_case_report_number_of_visits():
    """Test Case.report_number_of_visits returns expected data"""
    case: Case = Case.objects.create()

    assert case.report_number_of_visits == 0

    ReportVisitsMetrics.objects.create(case=case)
    ReportVisitsMetrics.objects.create(case=case)

    assert case.report_number_of_visits == 2


@pytest.mark.django_db
def test_case_report_number_of_unique_visitors():
    """Test Case.report_number_of_unique_visitors returns expected data"""
    case: Case = Case.objects.create()

    assert case.report_number_of_unique_visitors == 0

    ReportVisitsMetrics.objects.create(case=case)
    ReportVisitsMetrics.objects.create(case=case)

    assert case.report_number_of_unique_visitors == 1


@pytest.mark.django_db
def test_case_website_contact_links_count():
    """Test Case.website_contact_links_count returns expected data"""
    case: Case = Case.objects.create()

    assert case.website_contact_links_count == 0

    audit: Audit = Audit.objects.create(case=case)

    assert case.website_contact_links_count == 0

    Page.objects.create(audit=audit, page_type=Page.Type.CONTACT, url="url")

    assert case.website_contact_links_count == 1

    Page.objects.create(audit=audit, page_type=Page.Type.STATEMENT, url="url")

    assert case.website_contact_links_count == 2


def test_case_not_archived():
    """Test that Case.not_archived is true if Case.archived is empty"""
    case: Case = Case()

    assert case.not_archived is True

    case.archive = "archive"

    assert case.not_archived is False


@pytest.mark.django_db
def test_case_show_start_tests():
    """
    Test that Case.show_start_tests is true when no audit exists and
    the case is not archived
    """
    case: Case = Case.objects.create()

    assert case.show_start_test is True

    case.archive = "archive"

    assert case.show_start_test is False

    case.archive = ""

    assert case.show_start_test is True

    Audit.objects.create(case=case)

    assert case.show_start_test is False


@pytest.mark.django_db
def test_case_not_archived_has_audit():
    """
    Test that Case.not_archived_has_audit is true when audit exists and
    the case is not archived
    """
    case: Case = Case.objects.create()

    assert case.not_archived_has_audit is False

    Audit.objects.create(case=case)

    case: Case = Case.objects.get(id=case.id)

    assert case.not_archived_has_audit is True

    case.archive = "archive"

    assert case.not_archived_has_audit is False


def test_case_show_create_report_true():
    """Test that Case.show_create_report is true if Case has no report"""
    case: Case = Case()

    assert case.show_create_report is True


@pytest.mark.django_db
def test_case_show_create_report_false():
    """Test that Case.show_create_report is false if Case has a report"""
    case: Case = Case.objects.create()
    Report.objects.create(case=case)

    assert case.show_create_report is False


def test_case_not_archived_has_report_true():
    """Test that Case.not_archived_has_report is false if Case has no report"""
    case: Case = Case()

    assert case.not_archived_has_report is False


@pytest.mark.django_db
def test_case_not_archived_has_report_false():
    """Test that Case.not_archived_has_report is true if Case has a report"""
    case: Case = Case.objects.create()
    Report.objects.create(case=case)

    assert case.not_archived_has_report is True


@pytest.mark.django_db
def test_show_start_12_week_retest():
    """
    Test Case.show_start_12_week_retest true when Case is not achived,
    has an audit and the retest_date is not set.
    """
    case: Case = Case.objects.create()

    assert case.show_start_12_week_retest is False

    audit: Audit = Audit.objects.create(case=case)

    assert case.show_start_12_week_retest is True

    audit.retest_date = TODAY

    assert case.show_start_12_week_retest is False


@pytest.mark.django_db
def test_show_12_week_retest():
    """
    Test Case.show_12_week_retest true when Case is not achived,
    has an audit and the retest_date is set.
    """
    case: Case = Case.objects.create()

    assert case.show_12_week_retest is False

    audit: Audit = Audit.objects.create(case=case)

    assert case.show_12_week_retest is False

    audit.retest_date = TODAY

    assert case.show_12_week_retest is True


@pytest.mark.django_db
def test_overdue_link_seven_day_no_contact():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and no
    chaser emails have been sent.
    """
    case: Case = create_case_for_overdue_link()

    case.enable_correspondence_process = True
    case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    case.save()

    assert case.overdue_link is not None
    assert case.overdue_link.label == "No contact details response overdue"
    assert case.overdue_link.url == reverse(
        "cases:edit-request-contact-details", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_no_contact_one_week_chaser():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and only the
    one week chaser email has been sent.
    """
    case: Case = create_case_for_overdue_link()

    case.enable_correspondence_process = True
    case.seven_day_no_contact_email_sent_date = TWO_WEEKS_AGO
    case.no_contact_one_week_chaser_due_date = TODAY
    case.save()

    assert case.overdue_link is not None
    assert case.overdue_link.label == "No contact details response overdue"
    assert case.overdue_link.url == reverse(
        "cases:edit-request-contact-details", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_no_contact_four_week_chaser():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and only the
    four week chaser email has been sent.
    """
    case: Case = create_case_for_overdue_link()

    case.enable_correspondence_process = True
    case.seven_day_no_contact_email_sent_date = TWO_WEEKS_AGO
    case.no_contact_four_week_chaser_due_date = TODAY
    case.save()

    assert case.overdue_link is not None
    assert case.overdue_link.label == "No contact details response overdue"
    assert case.overdue_link.url == reverse(
        "cases:edit-request-contact-details", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_one_week_followup():
    """
    Check overdue link if case is in report correspondence,
    the one week followup is due but not sent.
    """
    case: Case = create_case_for_overdue_link()

    case.report_followup_week_1_due_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.IN_REPORT_CORES

    assert case.overdue_link is not None
    assert case.overdue_link.label == "1-week follow-up to report due"
    assert case.overdue_link.url == reverse(
        "cases:edit-report-one-week-followup", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_four_week_followup():
    """
    Check overdue link if case is in report correspondence,
    the four week followup is due but not sent.
    """
    case: Case = create_case_for_overdue_link()

    case.report_followup_week_4_due_date = ONE_WEEK_AGO
    case.report_followup_week_1_sent_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.IN_REPORT_CORES

    assert case.overdue_link is not None
    assert case.overdue_link.label == "4-week follow-up to report due"
    assert case.overdue_link.url == reverse(
        "cases:edit-report-four-week-followup", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_four_week_followup_sent_one_week_ago():
    """
    Check overdue link if case is in report correspondence,
    the four week followup was sent over a week ago.
    """
    case: Case = create_case_for_overdue_link()

    case.report_followup_week_4_due_date = FOUR_WEEKS_AGO
    case.report_followup_week_1_sent_date = FOUR_WEEKS_AGO
    case.report_followup_week_4_sent_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.IN_REPORT_CORES

    assert case.overdue_link is not None
    assert (
        case.overdue_link.label
        == "4-week follow-up to report sent, case needs to progress"
    )
    assert case.overdue_link.url == reverse(
        "cases:edit-report-acknowledged", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_12_week_deadline_due():
    """
    Check overdue link if case is awaiting 12-week deadline,
    the 12-week due date has passed.
    """
    case: Case = create_case_for_overdue_link()

    case.report_followup_week_12_due_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.AWAITING_12_WEEK_DEADLINE

    assert case.overdue_link is not None
    assert case.overdue_link.label == "12-week update due"
    assert case.overdue_link.url == reverse(
        "cases:edit-12-week-update-requested", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_12_week_correspondence_1_week_chaser_due():
    """
    Check overdue link if case is in 12-week correspondence,
    the 1-week chaser due date has passed.
    """
    case: Case = create_case_for_overdue_link()

    case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    case.twelve_week_1_week_chaser_due_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.IN_12_WEEK_CORES

    assert case.overdue_link is not None
    assert case.overdue_link.label == "1-week follow-up due"
    assert case.overdue_link.url == reverse(
        "cases:edit-12-week-one-week-followup-final", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_overdue_link_12_week_correspondence_1_week_chaser_sent_a_week_ago():
    """
    Check overdue link if case is in 12-week correspondence,
    the 1-week chaser was sent a week ago.
    """
    case: Case = create_case_for_overdue_link()

    case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    case.twelve_week_1_week_chaser_due_date = ONE_WEEK_AGO
    case.twelve_week_1_week_chaser_sent_date = ONE_WEEK_AGO
    case.save()
    case.status.status = CaseStatus.Status.IN_12_WEEK_CORES

    assert case.overdue_link is not None
    assert case.overdue_link.label == "1-week follow-up sent, case needs to progress"
    assert case.overdue_link.url == reverse(
        "cases:edit-12-week-update-request-ack", kwargs={"pk": case.id}
    )


@pytest.mark.django_db
def test_case_reminder():
    """Test Case.reminder returns the unread reminder"""
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    reminder: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        case=case,
        user=user,
        date=REMINDER_DUE_DATE,
    )

    assert case.reminder == reminder

    reminder.read = True
    reminder.save()

    assert case.reminder is None


@pytest.mark.django_db
def test_case_reminder_history():
    """Test Case.reminder_history returns the read reminders"""
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    reminder: Task = Task.objects.create(
        type=Task.Type.REMINDER,
        case=case,
        user=user,
        date=REMINDER_DUE_DATE,
    )

    assert case.reminder_history.count() == 0

    reminder.read = True
    reminder.save()

    assert case.reminder_history.count() == 1
    assert case.reminder_history.first() == reminder


@pytest.mark.django_db
def test_event_history_history_update():
    """Test EventHistory.variables contains expected values for update"""
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    event_history: EventHistory = EventHistory.objects.create(
        case=case,
        created_by=user,
        parent=case,
        difference=json.dumps({"notes": "Old note -> New note"}),
    )

    assert event_history.variables == [
        {
            "name": "notes",
            "old_value": "Old note",
            "new_value": "New note",
        }
    ]


@pytest.mark.django_db
def test_event_history_history_create():
    """Test EventHistory.variables contains expected values for create"""
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    event_history: EventHistory = EventHistory.objects.create(
        case=case,
        created_by=user,
        parent=case,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps({"notes": "Old note -> New note"}),
    )

    assert event_history.variables == [
        {
            "name": "notes",
            "old_value": "",
            "new_value": "Old note -> New note",
        }
    ]


@pytest.mark.django_db
def test_event_history_history_update_separator_in_text():
    """
    Test EventHistory.variables contains expected values for update
    when the separator (" -> ") appears in the data.
    """
    user: User = User.objects.create()
    case: Case = Case.objects.create()
    event_history: EventHistory = EventHistory.objects.create(
        case=case,
        created_by=user,
        parent=case,
        difference=json.dumps({"notes": "Old note -> New note -> separator"}),
    )

    assert event_history.variables == [
        {
            "name": "notes",
            "old_value": "Old note",
            "new_value": "New note -> separator",
        }
    ]
