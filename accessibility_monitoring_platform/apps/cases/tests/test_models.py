"""
Tests for cases models
"""
import pytest

import json
from datetime import date, datetime, timedelta, timezone
from typing import List
from unittest.mock import patch, Mock

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    PAGE_TYPE_STATEMENT,
    WcagDefinition,
    TEST_TYPE_AXE,
    CHECK_RESULT_ERROR,
    RETEST_CHECK_RESULT_FIXED,
    CONTENT_NOT_IN_SCOPE_VALID,
    StatementCheck,
    StatementCheckResult,
    STATEMENT_CHECK_NO,
    STATEMENT_CHECK_YES,
    STATEMENT_CHECK_TYPE_OVERVIEW,
    Retest,
    RETEST_INITIAL_COMPLIANCE_COMPLIANT,
)
from ...comments.models import Comment
from ...reminders.models import Reminder
from ...reports.models import Report
from ...s3_read_write.models import S3Report
from ..models import (
    Case,
    Contact,
    EqualityBodyCorrespondence,
    WEBSITE_COMPLIANCE_STATE_DEFAULT,
    WEBSITE_COMPLIANCE_STATE_DEFAULT,
    WEBSITE_COMPLIANCE_STATE_COMPLIANT,
    STATEMENT_COMPLIANCE_STATE_COMPLIANT,
    STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
    STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
    STATEMENT_COMPLIANCE_STATE_DEFAULT,
    EQUALITY_BODY_CORRESPONDENCE_QUESTION,
    EQUALITY_BODY_CORRESPONDENCE_RETEST,
    EQUALITY_BODY_CORRESPONDENCE_RESOLVED,
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

    assert str(case) == f"{case.organisation_name} | #{case.id}"


@pytest.mark.django_db
def test_case_title_is_organisation_name_bar_domain_bar_id():
    """Test the Case title string is organisation_name | url | id"""
    case: Case = Case.objects.create(
        home_page_url=HOME_PAGE_URL, organisation_name=ORGANISATION_NAME
    )

    assert (
        case.title
        == f"{case.organisation_name} | {case.formatted_home_page_url} | #{case.id}"
    )


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

    contacts: List[Contact] = list(Contact.objects.filter(case=case))

    assert contacts[0].id == contact2.id
    assert contacts[1].id == contact1.id


@pytest.mark.django_db
def test_preferred_contact_returned_first():
    """
    Test the contacts are returned in most recently created order with preferred contact first
    """
    case: Case = Case.objects.create()
    preferred_contact: Contact = Contact.objects.create(case=case, preferred="yes")
    contact1: Contact = Contact.objects.create(case=case)
    contact2: Contact = Contact.objects.create(case=case)

    contacts: List[Contact] = list(Contact.objects.filter(case=case))

    assert contacts[0].id == preferred_contact.id
    assert contacts[1].id == contact2.id
    assert contacts[2].id == contact1.id


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
        days=5
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
        (date.today() - timedelta(days=1), "past"),
        (date.today(), "present"),
        (date.today() + timedelta(days=1), "future"),
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

    comments: List[Contact] = case.qa_comments

    assert len(comments) == 2
    assert comments[0].id == comment2.id
    assert comments[1].id == comment1.id


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

    wcag_definition: WcagDefinition = WcagDefinition.objects.create(type=TEST_TYPE_AXE)
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CHECK_RESULT_CREATED)
    ):
        check_result: CheckResult = CheckResult.objects.create(
            audit=last_edited_audit,
            page=page,
            type=TEST_TYPE_AXE,
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
    """Test the case last edited date found on Reminder"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_REMINDER_UPDATED)
    ):
        Reminder.objects.create(case=last_edited_case, due_date=REMINDER_DUE_DATE)

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
        STATEMENT_COMPLIANCE_STATE_COMPLIANT
    )

    assert case.statement_checks_still_initial is False

    audit: Audit = Audit.objects.create(case=case)
    for statement_check in StatementCheck.objects.filter(
        type=STATEMENT_CHECK_TYPE_OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    assert case.statement_checks_still_initial is True

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = STATEMENT_CHECK_YES
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
            WEBSITE_COMPLIANCE_STATE_DEFAULT,
            WEBSITE_COMPLIANCE_STATE_DEFAULT,
            "Not known",
        ),
        (WEBSITE_COMPLIANCE_STATE_DEFAULT, "compliant", "Fully compliant"),
        (
            WEBSITE_COMPLIANCE_STATE_DEFAULT,
            "partially-compliant",
            "Partially compliant",
        ),
        (
            WEBSITE_COMPLIANCE_STATE_COMPLIANT,
            WEBSITE_COMPLIANCE_STATE_DEFAULT,
            "Fully compliant",
        ),
        (
            "partially-compliant",
            WEBSITE_COMPLIANCE_STATE_DEFAULT,
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


@pytest.mark.parametrize(
    "statement_compliance_state_initial, statement_compliance_state_12_week, expected_result",
    [
        (
            STATEMENT_COMPLIANCE_STATE_COMPLIANT,
            STATEMENT_COMPLIANCE_STATE_DEFAULT,
            "Compliant",
        ),
        ("not-compliant", STATEMENT_COMPLIANCE_STATE_DEFAULT, "Not compliant"),
        ("not-found", STATEMENT_COMPLIANCE_STATE_DEFAULT, "Not found"),
        ("other", STATEMENT_COMPLIANCE_STATE_DEFAULT, "Other"),
        (
            STATEMENT_COMPLIANCE_STATE_DEFAULT,
            STATEMENT_COMPLIANCE_STATE_DEFAULT,
            "Not selected",
        ),
        (
            STATEMENT_COMPLIANCE_STATE_DEFAULT,
            STATEMENT_COMPLIANCE_STATE_COMPLIANT,
            "Compliant",
        ),
        (STATEMENT_COMPLIANCE_STATE_DEFAULT, "not-compliant", "Not compliant"),
        (STATEMENT_COMPLIANCE_STATE_DEFAULT, "not-found", "Not found"),
        (STATEMENT_COMPLIANCE_STATE_DEFAULT, "other", "Other"),
    ],
)
@pytest.mark.django_db
def test_accessibility_statement_compliance_display(
    statement_compliance_state_initial,
    statement_compliance_state_12_week,
    expected_result,
):
    """Test accessibility statement compliance is derived correctly"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_initial=statement_compliance_state_initial,
        statement_compliance_state_12_week=statement_compliance_state_12_week,
    )

    assert case.accessibility_statement_compliance_display == expected_result


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
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(type=TEST_TYPE_AXE)
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=TEST_TYPE_AXE,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )

    assert case.percentage_website_issues_fixed == 0

    check_result.retest_state = RETEST_CHECK_RESULT_FIXED
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
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(type=TEST_TYPE_AXE)
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=TEST_TYPE_AXE,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )

    assert case.overview_issues_website == "0 of 1 fixed (0%)"

    check_result.retest_state = RETEST_CHECK_RESULT_FIXED
    check_result.save()

    assert case.overview_issues_website == "1 of 1 fixed (100%)"


@pytest.mark.django_db
def test_overview_issues_statement_with_audit():
    """Test that case with audit returns overview"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)

    assert case.overview_issues_statement == "0 of 12 fixed (0%)"

    audit.archive_audit_retest_content_not_in_scope_state = CONTENT_NOT_IN_SCOPE_VALID
    audit.save()

    assert case.overview_issues_statement == "1 of 12 fixed (8%)"


@pytest.mark.django_db
def test_overview_issues_statement_with_statement_checks():
    """Test that case with audit returns overview"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for count, statement_check in enumerate(StatementCheck.objects.all()):
        check_result_state: str = (
            STATEMENT_CHECK_NO if count % 2 == 0 else STATEMENT_CHECK_YES
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
            statement_check_result.check_result_state = STATEMENT_CHECK_YES
            statement_check_result.save()

    assert case.overview_issues_statement == "10 checks failed on test"


@pytest.mark.django_db
def test_set_accessibility_statement_state_default():
    """Test calculated accessibility statement state for new case"""
    case: Case = Case.objects.create()

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_initial
        == STATEMENT_COMPLIANCE_STATE_DEFAULT
    )


@pytest.mark.parametrize(
    "statement_compliance_state_initial",
    [
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_initial_no_audit(
    statement_compliance_state_initial,
):
    """Test statement_compliance_state_initial unchanged in case with no audit"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_initial=statement_compliance_state_initial
    )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_initial
        == statement_compliance_state_initial
    )


@pytest.mark.parametrize(
    "statement_compliance_state_initial",
    [
        STATEMENT_COMPLIANCE_STATE_DEFAULT,
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_initial_no_statement_page(
    statement_compliance_state_initial,
):
    """Test statement_compliance_state_initial not compliant in case with no statement page"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_initial=statement_compliance_state_initial
    )
    Audit.objects.create(case=case)

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_initial
        == STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
    )


@pytest.mark.parametrize(
    "statement_compliance_state_initial",
    [
        STATEMENT_COMPLIANCE_STATE_DEFAULT,
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_initial_no_statement_checks(
    statement_compliance_state_initial,
):
    """
    Test statement_compliance_state_initial unchanged in case which doesn't
    use statement checks.
    """
    case: Case = create_case_and_compliance(
        statement_compliance_state_initial=statement_compliance_state_initial
    )
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_initial
        == statement_compliance_state_initial
    )


@pytest.mark.django_db
def test_set_statement_compliance_state_initial_to_compliant():
    """
    Test statement_compliance_state_initial set to compliant when no statement check
    has been answered 'no'.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )
    for statement_check in StatementCheck.objects.filter(
        type=STATEMENT_CHECK_TYPE_OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_initial
        == STATEMENT_COMPLIANCE_STATE_COMPLIANT
    )


@pytest.mark.django_db
def test_set_statement_compliance_state_initial_to_not_compliant():
    """
    Test statement_compliance_state_initial set to not compliant when a statement check
    has been answered 'no'.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )
    for statement_check in StatementCheck.objects.filter(
        type=STATEMENT_CHECK_TYPE_OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=STATEMENT_CHECK_NO,
        )

    case.set_statement_compliance_states()
    assert (
        case.compliance.statement_compliance_state_initial
        == STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
    )


@pytest.mark.django_db
def test_set_statement_compliance_state_12_week_default():
    """Test calculated final accessibility statement state for new case"""
    case: Case = Case.objects.create()

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == STATEMENT_COMPLIANCE_STATE_DEFAULT
    )


@pytest.mark.parametrize(
    "statement_compliance_state_12_week",
    [
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_12_week_no_audit(
    statement_compliance_state_12_week,
):
    """Test statement_compliance_state_12_week unchanged in case with no audit"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_12_week=statement_compliance_state_12_week
    )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == statement_compliance_state_12_week
    )


@pytest.mark.parametrize(
    "statement_compliance_state_12_week",
    [
        STATEMENT_COMPLIANCE_STATE_DEFAULT,
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_12_week__no_statement_page(
    statement_compliance_state_12_week,
):
    """Test statement_compliance_state_12_week not compliant in case with no statement page"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_12_week=statement_compliance_state_12_week
    )
    Audit.objects.create(case=case)

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
    )


@pytest.mark.parametrize(
    "statement_compliance_state_12_week",
    [
        STATEMENT_COMPLIANCE_STATE_DEFAULT,
        STATEMENT_COMPLIANCE_STATE_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT,
        STATEMENT_COMPLIANCE_STATE_NOT_FOUND,
        "other",
    ],
)
@pytest.mark.django_db
def test_set_statement_compliance_state_12_week_no_statement_checks(
    statement_compliance_state_12_week,
):
    """Test statement_compliance_state_12_week unchanged in case with no statement page"""
    case: Case = create_case_and_compliance(
        statement_compliance_state_12_week=statement_compliance_state_12_week
    )
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == statement_compliance_state_12_week
    )


@pytest.mark.django_db
def test_set_statement_compliance_state_12_week_to_compliant():
    """
    Test statement_compliance_state_12_week set to compliant when no statement check
    retest state has been set to 'no'.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )
    for statement_check in StatementCheck.objects.filter(
        type=STATEMENT_CHECK_TYPE_OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == STATEMENT_COMPLIANCE_STATE_COMPLIANT
    )


@pytest.mark.django_db
def test_set_statement_compliance_state_12_week_to_not_compliant():
    """
    Test statement_compliance_state_12_week set to not compliant when a statement check
    retest state has been set to 'no'.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    Page.objects.create(
        audit=audit, page_type=PAGE_TYPE_STATEMENT, url="https://example.com"
    )
    for statement_check in StatementCheck.objects.filter(
        type=STATEMENT_CHECK_TYPE_OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            retest_state=STATEMENT_CHECK_NO,
        )

    case.set_statement_compliance_states()

    assert (
        case.compliance.statement_compliance_state_12_week
        == STATEMENT_COMPLIANCE_STATE_NOT_COMPLIANT
    )


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

    incomplete_retest.retest_compliance_state = RETEST_INITIAL_COMPLIANCE_COMPLIANT
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
def test_case_equality_body_questions_returns_equality_body_questions():
    """Test Case.equality_body_questions returns equality_body_questions"""
    case: Case = Case.objects.create()
    equality_body_question: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EQUALITY_BODY_CORRESPONDENCE_QUESTION
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
            case=case, type=EQUALITY_BODY_CORRESPONDENCE_QUESTION
        )
    )

    assert len(case.equality_body_questions_unresolved) == 1
    assert case.equality_body_questions_unresolved[0] == unresolved_question

    unresolved_question.status = EQUALITY_BODY_CORRESPONDENCE_RESOLVED
    unresolved_question.save()

    assert len(case.equality_body_questions_unresolved) == 0


@pytest.mark.django_db
def test_case_equality_body_correspondence_retests_returns_equality_body_correspondence_retests():
    """Test Case.equality_body_correspondence_retests returns equality_body_correspondence_retests"""
    case: Case = Case.objects.create()
    equality_body_retest: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            case=case, type=EQUALITY_BODY_CORRESPONDENCE_RETEST
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
            case=case, type=EQUALITY_BODY_CORRESPONDENCE_RETEST
        )
    )

    assert len(case.equality_body_correspondence_retests_unresolved) == 1
    assert case.equality_body_correspondence_retests_unresolved[0] == unresolved_retest

    unresolved_retest.status = EQUALITY_BODY_CORRESPONDENCE_RESOLVED
    unresolved_retest.save()

    assert len(case.equality_body_correspondence_retests_unresolved) == 0
