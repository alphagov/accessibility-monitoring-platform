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
from ...common.models import Boolean, EmailTemplate, Link
from ...detailed.models import DetailedCase
from ...notifications.models import Task
from ...reports.models import Report, ReportVisitsMetrics
from ...s3_read_write.models import S3Report
from ..models import (
    CaseCompliance,
    CaseStatus,
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    SimplifiedCaseHistory,
    SimplifiedEventHistory,
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


def create_case_for_overdue_link() -> SimplifiedCase:
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        created=datetime.now().tzinfo,
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        reviewer=user,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )
    simplified_case.update_case_status()
    return simplified_case


@pytest.fixture
def last_edited_case() -> SimplifiedCase:
    """Pytest fixture case for testing last edited timestamp values"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_CASE_CREATED)):
        return SimplifiedCase.objects.create()


@pytest.fixture
def last_edited_audit(last_edited_case: SimplifiedCase) -> Audit:
    """Pytest fixture audit for testing last edited timestamp values"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_CREATED)):
        return Audit.objects.create(
            simplified_case=last_edited_case, date_of_test=DATE_AUDIT_CREATED
        )


@pytest.mark.django_db
def test_case_number_incremented_on_creation():
    """Test that each new case gets the next case_number"""
    simplified_case_one: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case_one.case_number == 1

    simplified_case_two: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case_two.case_number == 2


@pytest.mark.django_db
def test_case_created_timestamp_is_populated():
    """Test the Case created field is populated the first time the Case is saved"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.created is not None
    assert isinstance(simplified_case.created, datetime)


@pytest.mark.django_db
def test_case_created_timestamp_is_not_updated():
    """Test the Case created field is not updated on subsequent saves"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    original_created_timestamp: datetime = simplified_case.created
    updated_organisation_name: str = "updated organisation name"
    simplified_case.organisation_name = updated_organisation_name
    simplified_case.save()
    updated_case: SimplifiedCase = SimplifiedCase.objects.get(pk=simplified_case.id)

    assert updated_case.organisation_name == updated_organisation_name
    assert updated_case.created == original_created_timestamp


@pytest.mark.django_db
def test_case_domain_is_populated_from_home_page_url():
    """Test the Case domain field is populated from the home_page_url"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL
    )

    assert simplified_case.domain == DOMAIN


@pytest.mark.django_db
def test_case_renders_as_organisation_name_bar_id():
    """Test the Case string is organisation_name | id"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    assert (
        str(simplified_case)
        == f"{simplified_case.organisation_name} | {simplified_case.case_identifier}"
    )


@pytest.mark.django_db
def test_case_title_is_organisation_name_bar_id():
    """Test the Case title string is organisation_name | id"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL, organisation_name=ORGANISATION_NAME
    )

    assert (
        simplified_case.title
        == f"{simplified_case.organisation_name} &nbsp;|&nbsp; {simplified_case.case_identifier}"
    )


@pytest.mark.django_db
def test_case_completed_timestamp_is_updated_on_completion():
    """Test the Case completed date field is updated when case_completed is set"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.completed_date is None

    simplified_case.case_completed = "no-action"
    simplified_case.save()
    updated_case: SimplifiedCase = SimplifiedCase.objects.get(pk=simplified_case.id)

    assert updated_case.completed_date is not None
    assert isinstance(updated_case.completed_date, datetime)


@pytest.mark.django_db
def test_contact_created_timestamp_is_populated():
    """Test the created field is populated the first time the Contact is saved"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(simplified_case=simplified_case)

    assert contact.created is not None
    assert isinstance(contact.created, datetime)


@pytest.mark.django_db
def test_contact_created_timestamp_is_not_updated():
    """Test the created field is not updated on subsequent save"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(simplified_case=simplified_case)

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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact1: Contact = Contact.objects.create(simplified_case=simplified_case)
    contact2: Contact = Contact.objects.create(simplified_case=simplified_case)

    contacts: list[Contact] = list(simplified_case.contacts)

    assert contacts[0].id == contact2.id
    assert contacts[1].id == contact1.id


@pytest.mark.django_db
def test_deleted_contacts_not_returned():
    """Test that deleted contacts are not returned"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact1: Contact = Contact.objects.create(simplified_case=simplified_case)
    contact2: Contact = Contact.objects.create(simplified_case=simplified_case)

    contacts: list[Contact] = list(simplified_case.contacts)

    assert len(contacts) == 2

    contact1.is_deleted = True
    contact1.save()

    contacts: list[Contact] = list(simplified_case.contacts)

    assert len(contacts) == 1
    assert contacts[0].id == contact2.id


@pytest.mark.django_db
def test_preferred_contact_returned_first():
    """
    Test the contacts are returned in most recently created order with preferred contact first
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    preferred_contact: Contact = Contact.objects.create(
        simplified_case=simplified_case, preferred="yes"
    )
    contact1: Contact = Contact.objects.create(simplified_case=simplified_case)
    contact2: Contact = Contact.objects.create(simplified_case=simplified_case)

    contacts: list[Contact] = list(simplified_case.contacts)

    assert contacts[0].id == preferred_contact.id
    assert contacts[1].id == contact2.id
    assert contacts[2].id == contact1.id


@pytest.mark.django_db
def test_contact_exists():
    """Test the contacts exists"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.contact_exists is False

    Contact.objects.create(simplified_case=simplified_case)

    assert simplified_case.contact_exists is True


@pytest.mark.parametrize(
    "compliance_email_sent_date, expected_psb_appeal_deadline",
    [
        (None, None),
        (date(2020, 1, 1), date(2020, 1, 29)),
    ],
)
def test_psb_appeal_deadline(compliance_email_sent_date, expected_psb_appeal_deadline):
    simplified_case: SimplifiedCase = SimplifiedCase(
        compliance_email_sent_date=compliance_email_sent_date
    )

    assert simplified_case.psb_appeal_deadline == expected_psb_appeal_deadline


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
    simplified_case: SimplifiedCase = SimplifiedCase(home_page_url=url)
    assert simplified_case.formatted_home_page_url == expected_formatted_url


@pytest.mark.django_db
def test_next_action_due_date_for_report_ready_to_send():
    """
    Check that the next_action_due_date is correctly returned
    when case status is report ready to send.
    """
    seven_day_no_contact_email_sent_date: date = NO_CONTACT_DATE
    no_contact_one_week_chaser_due_date: date = NO_CONTACT_ONE_WEEK
    no_contact_four_week_chaser_due_date: date = NO_CONTACT_FOUR_WEEKS

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        seven_day_no_contact_email_sent_date=seven_day_no_contact_email_sent_date,
        no_contact_one_week_chaser_due_date=no_contact_one_week_chaser_due_date,
        no_contact_four_week_chaser_due_date=no_contact_four_week_chaser_due_date,
        status=SimplifiedCase.Status.REPORT_READY_TO_SEND,
    )

    # Initial no countact details request sent
    assert simplified_case.next_action_due_date == no_contact_one_week_chaser_due_date

    simplified_case.no_contact_one_week_chaser_sent_date = NO_CONTACT_ONE_WEEK

    # No contact details 1-week chaser sent
    assert simplified_case.next_action_due_date == no_contact_four_week_chaser_due_date

    simplified_case.no_contact_four_week_chaser_sent_date = NO_CONTACT_FOUR_WEEKS

    # No contact details 4-week chaser sent
    assert simplified_case.next_action_due_date == NO_CONTACT_FOUR_WEEKS + timedelta(
        days=7
    )


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

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_1_sent_date=any_old_date,
        report_followup_week_4_sent_date=any_old_date,
        report_followup_week_1_due_date=report_followup_week_1_due_date,
        report_followup_week_4_due_date=report_followup_week_4_due_date,
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        status=SimplifiedCase.Status.IN_REPORT_CORES,
    )

    simplified_case.report_followup_week_4_sent_date = None
    assert simplified_case.next_action_due_date == report_followup_week_4_due_date

    simplified_case.report_followup_week_1_sent_date = None
    assert simplified_case.next_action_due_date == report_followup_week_1_due_date


@pytest.mark.django_db
def test_next_action_due_date_for_in_probation_period():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in probation period.
    """
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
    )

    assert simplified_case.next_action_due_date == report_followup_week_12_due_date


@pytest.mark.django_db
def test_next_action_due_date_for_in_12_week_correspondence():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in 12-week correspondence.
    """
    twelve_week_1_week_chaser_due_date: date = date(2020, 1, 1)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
        status=SimplifiedCase.Status.AFTER_12_WEEK_CORES,
    )

    assert simplified_case.next_action_due_date == twelve_week_1_week_chaser_due_date

    twelve_week_1_week_chaser_sent_date: date = date(2020, 1, 1)
    simplified_case.twelve_week_1_week_chaser_sent_date = (
        twelve_week_1_week_chaser_sent_date
    )

    assert (
        simplified_case.next_action_due_date
        == twelve_week_1_week_chaser_sent_date + timedelta(days=7)
    )


@pytest.mark.parametrize(
    "status",
    [
        "unknown",
        SimplifiedCase.Status.UNASSIGNED,
        SimplifiedCase.Status.TEST_IN_PROGRESS,
        SimplifiedCase.Status.REPORT_IN_PROGRESS,
        SimplifiedCase.Status.READY_TO_QA,
        SimplifiedCase.Status.QA_IN_PROGRESS,
        SimplifiedCase.Status.REPORT_READY_TO_SEND,
        SimplifiedCase.Status.FINAL_DECISION_DUE,
        SimplifiedCase.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
        SimplifiedCase.Status.COMPLETE,
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

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
    )

    assert simplified_case.next_action_due_date == date(1970, 1, 1)


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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        status=SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE,
    )

    assert simplified_case.next_action_due_date_tense == expected_tense


@pytest.mark.django_db
def test_case_save_increments_version():
    """Test that saving a Case increments its version"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    old_version: int = simplified_case.version
    simplified_case.save()

    assert simplified_case.version == old_version + 1


@pytest.mark.parametrize(
    "previous_case_url, previous_case_identifier",
    [
        ("https://...gov.uk/simplified/1/view/", "#S-1"),
        ("https://...gov.uk/detailed/1/case-detail/", "#D-1"),
        ("", None),
        ("https://...gov.uk/audit/191/view/", None),
    ],
)
@pytest.mark.django_db
def test_previous_case_identifier(previous_case_url, previous_case_identifier):
    """Test previous case identifier derived from url"""
    if "detailed" in previous_case_url:
        DetailedCase.objects.create()
    else:
        SimplifiedCase.objects.create()

    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        previous_case_url=previous_case_url
    )

    assert simplified_case.previous_case_identifier == previous_case_identifier


@pytest.mark.django_db
def test_case_last_edited_from_case(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on Case"""
    assert last_edited_case.last_edited == DATETIME_CASE_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_CASE_UPDATED)):
        last_edited_case.save()

    assert last_edited_case.last_edited == DATETIME_CASE_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_contact(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on Contact"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CONTACT_CREATED)
    ):
        contact: Contact = Contact.objects.create(simplified_case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_CONTACT_CREATED

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_CONTACT_UPDATED)
    ):
        contact.save()

    assert last_edited_case.last_edited == DATETIME_CONTACT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_audit(
    last_edited_case: SimplifiedCase, last_edited_audit: Audit
):
    """Test the case last edited date found on Audit"""
    assert last_edited_case.last_edited == DATETIME_AUDIT_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_AUDIT_UPDATED)):
        last_edited_audit.save()

    assert last_edited_case.last_edited == DATETIME_AUDIT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_page(
    last_edited_case: SimplifiedCase, last_edited_audit: Audit
):
    """Test the case last edited date found on Page"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_CREATED)):
        page: Page = Page.objects.create(audit=last_edited_audit)

    assert last_edited_case.last_edited == DATETIME_PAGE_CREATED

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_PAGE_UPDATED)):
        page.save()

    assert last_edited_case.last_edited == DATETIME_PAGE_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_check_result(
    last_edited_case: SimplifiedCase, last_edited_audit: Audit
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
def test_case_last_edited_from_comment(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on Comment"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_CREATED)
    ):
        comment: Comment = Comment.objects.create(base_case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_COMMENT_CREATED

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_UPDATED)
    ):
        comment.save()

    assert last_edited_case.last_edited == DATETIME_COMMENT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_reminder(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on reminder Task"""
    user: User = User.objects.create()
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_REMINDER_UPDATED)
    ):
        Task.objects.create(
            type=Task.Type.REMINDER,
            base_case=last_edited_case,
            user=user,
            date=REMINDER_DUE_DATE,
        )

    assert last_edited_case.last_edited == DATETIME_REMINDER_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_report(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on Report"""
    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_REPORT_UPDATED)):
        Report.objects.create(base_case=last_edited_case)

    assert last_edited_case.last_edited == DATETIME_REPORT_UPDATED


@pytest.mark.django_db
def test_case_last_edited_from_s3_report(last_edited_case: SimplifiedCase):
    """Test the case last edited date found on S3Report"""
    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_S3REPORT_UPDATED)
    ):
        S3Report.objects.create(base_case=last_edited_case, version=0)

    assert last_edited_case.last_edited == DATETIME_S3REPORT_UPDATED


@pytest.mark.django_db
def test_case_statement_checks_still_initial():
    """
    Test statement state has not been determined. Either because the statement
    state is still the default or, if statement checks exist, one of the
    overview checks is still not tested.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)

    assert simplified_case.statement_checks_still_initial is True

    simplified_case.compliance.statement_compliance_state_initial = (
        CaseCompliance.StatementCompliance.COMPLIANT
    )

    assert simplified_case.statement_checks_still_initial is False

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
        )

    assert simplified_case.statement_checks_still_initial is True

    for statement_check_result in audit.overview_statement_check_results:
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert simplified_case.statement_checks_still_initial is False


@pytest.mark.django_db
def test_contact_updated_updated():
    """Test the contact updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    contact: Contact = Contact.objects.create(simplified_case=simplified_case)

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
    simplified_case: SimplifiedCase = create_case_and_compliance(
        website_compliance_state_initial=website_compliance_state_initial,
        website_compliance_state_12_week=website_compliance_state_12_week,
    )

    assert simplified_case.website_compliance_display == expected_result


@pytest.mark.django_db
def test_percentage_website_issues_fixed_no_audit():
    """Test that cases without audits return n/a"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.percentage_website_issues_fixed == "n/a"


@pytest.mark.django_db
def test_overview_issues_website_with_audit_no_issues():
    """Test that case with audit but no issues returns n/a"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.percentage_website_issues_fixed == "n/a"


@pytest.mark.django_db
def test_percentage_website_issues_fixed_with_audit_and_issues():
    """Test that case with audit and issues returns percentage"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
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

    assert simplified_case.percentage_website_issues_fixed == 0

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    assert simplified_case.percentage_website_issues_fixed == 100


@pytest.mark.django_db
def test_overview_issues_website_no_audit():
    """Test that cases without audits return no test exists"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.overview_issues_website == "No test exists"


@pytest.mark.django_db
def test_overview_issues_statement_no_audit():
    """Test that cases without audits return no test exists"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.overview_issues_statement == "No test exists"


@pytest.mark.django_db
def test_overview_issues_website_with_audit():
    """Test that case with audit returns overview"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.overview_issues_website == "0 of 0 fixed"

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

    assert simplified_case.overview_issues_website == "0 of 1 fixed (0%)"

    check_result.retest_state = CheckResult.RetestResult.FIXED
    check_result.save()

    assert simplified_case.overview_issues_website == "1 of 1 fixed (100%)"


@pytest.mark.django_db
def test_overview_issues_statement_with_statement_checks():
    """Test that case with audit returns overview"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    audit: Audit = Audit.objects.create(simplified_case=simplified_case)
    for count, statement_check in enumerate(
        StatementCheck.objects.filter(date_end=None)
    ):
        if count == 20:
            break
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

    assert simplified_case.overview_issues_statement == "10 checks failed on test"

    for count, statement_check_result in enumerate(
        audit.failed_statement_check_results
    ):
        if count % 2 == 0:
            statement_check_result.check_result_state = StatementCheckResult.Result.YES
            statement_check_result.save()

    assert simplified_case.overview_issues_statement == "5 checks failed on test"


def test_archived_sections():
    """Test archived sections"""
    simplified_case: SimplifiedCase = SimplifiedCase()

    assert simplified_case.archived_sections is None

    simplified_case.archive = json.dumps({"sections": ["section_one"]})

    assert len(simplified_case.archived_sections) == 1
    assert simplified_case.archived_sections[0] == "section_one"


@pytest.mark.django_db
def test_equality_body_correspondence_sets_id_within_case():
    """Test EqualityBodyCorrespondence sets id_within_case on save"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    first_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(simplified_case=simplified_case)
    )

    assert first_equality_body_correspondence.id_within_case == 1

    second_equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(simplified_case=simplified_case)
    )

    assert second_equality_body_correspondence.id_within_case == 2


@pytest.mark.django_db
def test_case_retests_returns_undeleted_retests():
    """Test SimplifiedCase.retests returns undeleted retests"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    assert len(simplified_case.retests) == 1
    assert simplified_case.retests[0] == retest

    retest.is_deleted = True
    retest.save()

    assert len(simplified_case.retests) == 0


@pytest.mark.django_db
def test_case_number_retests():
    """
    Test SimplifiedCase.number_retests returns number of retests not counting
    Retest #0.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Retest.objects.create(simplified_case=simplified_case)

    assert simplified_case.number_retests == 1

    Retest.objects.create(simplified_case=simplified_case, id_within_case=0)

    assert simplified_case.number_retests == 1


@pytest.mark.django_db
def test_case_latest_retest_returns_most_recent():
    """Test SimplifiedCase.latest_retest returns most recent"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.latest_retest is None

    first_retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    assert simplified_case.latest_retest == first_retest

    second_retest: Retest = Retest.objects.create(
        simplified_case=simplified_case, id_within_case=2
    )

    assert simplified_case.latest_retest == second_retest


@pytest.mark.django_db
def test_case_incomplete_retests_returns_incomplete_retests():
    """Test SimplifiedCase.incomplete_retests returns retests with the default state"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    incomplete_retest: Retest = Retest.objects.create(simplified_case=simplified_case)

    assert len(simplified_case.incomplete_retests) == 1
    assert simplified_case.incomplete_retests[0] == incomplete_retest

    incomplete_retest.retest_compliance_state = Retest.Compliance.COMPLIANT
    incomplete_retest.save()

    assert len(simplified_case.incomplete_retests) == 0


@pytest.mark.django_db
def test_case_equality_body_correspondences_returns_undeleted_equality_body_correspondences():
    """Test SimplifiedCase.equality_body_correspondences returns undeleted equality_body_correspondences"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(simplified_case=simplified_case)
    )

    assert len(simplified_case.equality_body_correspondences) == 1
    assert (
        simplified_case.equality_body_correspondences[0] == equality_body_correspondence
    )

    equality_body_correspondence.is_deleted = True
    equality_body_correspondence.save()

    assert len(simplified_case.equality_body_questions) == 0


@pytest.mark.django_db
def test_equality_body_correspondences_unresolved_count():
    """
    Test SimplifiedCase.equality_body_correspondences_unresolved_count returns number of
    unresolved equality_body_correspondences.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_correspondence: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(simplified_case=simplified_case)
    )

    assert simplified_case.equality_body_correspondences_unresolved_count == 1

    equality_body_correspondence.status = EqualityBodyCorrespondence.Status.RESOLVED
    equality_body_correspondence.save()

    assert simplified_case.equality_body_correspondences_unresolved_count == 0


@pytest.mark.django_db
def test_case_equality_body_questions_returns_equality_body_questions():
    """Test SimplifiedCase.equality_body_questions returns equality_body_questions"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_question: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            simplified_case=simplified_case,
            type=EqualityBodyCorrespondence.Type.QUESTION,
        )
    )

    assert len(simplified_case.equality_body_questions) == 1
    assert simplified_case.equality_body_questions[0] == equality_body_question


@pytest.mark.django_db
def test_case_equality_body_questions_unresolved_returns_unresolved():
    """Test SimplifiedCase.equality_body_questions_unresolved returns questions with the default state"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    unresolved_question: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            simplified_case=simplified_case,
            type=EqualityBodyCorrespondence.Type.QUESTION,
        )
    )

    assert len(simplified_case.equality_body_questions_unresolved) == 1
    assert simplified_case.equality_body_questions_unresolved[0] == unresolved_question

    unresolved_question.status = EqualityBodyCorrespondence.Status.RESOLVED
    unresolved_question.save()

    assert len(simplified_case.equality_body_questions_unresolved) == 0


@pytest.mark.django_db
def test_case_equality_body_correspondence_retests_returns_equality_body_correspondence_retests():
    """Test SimplifiedCase.equality_body_correspondence_retests returns equality_body_correspondence_retests"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    equality_body_retest: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            simplified_case=simplified_case, type=EqualityBodyCorrespondence.Type.RETEST
        )
    )

    assert len(simplified_case.equality_body_correspondence_retests) == 1
    assert (
        simplified_case.equality_body_correspondence_retests[0] == equality_body_retest
    )


@pytest.mark.django_db
def test_case_equality_body_correspondence_retests_unresolved_returns_unresolved():
    """Test SimplifiedCase.equality_body_correspondence_retests_unresolved returns retests with the default state"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    unresolved_retest: EqualityBodyCorrespondence = (
        EqualityBodyCorrespondence.objects.create(
            simplified_case=simplified_case, type=EqualityBodyCorrespondence.Type.RETEST
        )
    )

    assert len(simplified_case.equality_body_correspondence_retests_unresolved) == 1
    assert (
        simplified_case.equality_body_correspondence_retests_unresolved[0]
        == unresolved_retest
    )

    unresolved_retest.status = EqualityBodyCorrespondence.Status.RESOLVED
    unresolved_retest.save()

    assert len(simplified_case.equality_body_correspondence_retests_unresolved) == 0


@pytest.mark.django_db
def test_calulate_qa_status_unassigned():
    """Test Case calulate_qa_status correctly returns unassigned"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_review_status=Boolean.YES
    )

    assert simplified_case.calulate_qa_status() == SimplifiedCase.QAStatus.UNASSIGNED


@pytest.mark.django_db
def test_calulate_qa_status_in_qa():
    """Test Case calulate_qa_status correctly returns In-QA"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        reviewer=user,
        report_review_status=Boolean.YES,
    )

    assert simplified_case.calulate_qa_status() == SimplifiedCase.QAStatus.IN_QA


@pytest.mark.django_db
def test_calulate_qa_status_approved():
    """Test Case calulate_qa_status correctly returns approved"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
    )

    assert simplified_case.calulate_qa_status() == SimplifiedCase.QAStatus.APPROVED


@pytest.mark.django_db
def test_total_website_issues():
    """Test Case total_website_issues returns number found or n/a if none"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.total_website_issues == 0

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.total_website_issues == 0

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

    assert simplified_case.total_website_issues == 2


@pytest.mark.django_db
def test_total_website_issues_fixed():
    """Test Case total_website_issues_fixed returns number found or n/a if none"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.total_website_issues_fixed == 0

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.total_website_issues_fixed == 0

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

    assert simplified_case.total_website_issues_fixed == 1


@pytest.mark.django_db
def test_total_website_issues_unfixed():
    """Test Case total_website_issues_unfixed returns number found or n/a if none"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.total_website_issues_unfixed == 0

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.total_website_issues_unfixed == 0

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

    assert simplified_case.total_website_issues_unfixed == 1


@pytest.mark.django_db
def test_csv_export_statement_initially_found():
    """Test Case csv_export_statement_initially_found"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.csv_export_statement_initially_found == "unknown"

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            check_result_state=StatementCheckResult.Result.NO,
        )

    assert simplified_case.csv_export_statement_initially_found == "No"

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.check_result_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert simplified_case.csv_export_statement_initially_found == "Yes"


@pytest.mark.django_db
def test_csv_export_statement_found_at_12_week_retest():
    """Test Case csv_export_statement_found_at_12_week_retest"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.csv_export_statement_found_at_12_week_retest == "unknown"

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    for statement_check in StatementCheck.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        StatementCheckResult.objects.create(
            audit=audit,
            type=statement_check.type,
            statement_check=statement_check,
            retest_state=StatementCheckResult.Result.NO,
        )

    assert simplified_case.csv_export_statement_found_at_12_week_retest == "No"

    for statement_check_result in StatementCheckResult.objects.filter(
        type=StatementCheck.Type.OVERVIEW
    ):
        statement_check_result.retest_state = StatementCheckResult.Result.YES
        statement_check_result.save()

    assert simplified_case.csv_export_statement_found_at_12_week_retest == "Yes"


@pytest.mark.django_db
def test_case_latest_psb_zendesk_url():
    """Test SimplifiedCase.latest_psb_zendesk_url"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.latest_psb_zendesk_url == ""

    simplified_case.zendesk_url = "first"
    simplified_case.save()

    assert simplified_case.latest_psb_zendesk_url == "first"

    ZendeskTicket.objects.create(simplified_case=simplified_case, url="second")

    assert simplified_case.latest_psb_zendesk_url == "second"


@pytest.mark.django_db
def test_case_zendesk_tickets():
    """Test SimplifiedCase.zendesk_tickets"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        simplified_case=simplified_case
    )

    assert simplified_case.zendesk_tickets.count() == 1
    assert simplified_case.zendesk_tickets.first() == zendesk_ticket

    zendesk_ticket.is_deleted = True
    zendesk_ticket.save()

    assert simplified_case.zendesk_tickets.count() == 0


@pytest.mark.django_db
def test_zendesk_ticket_get_absolute_url():
    """Test ZendeskTickets.get_absolute_url"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        simplified_case=simplified_case
    )

    assert zendesk_ticket.get_absolute_url() == "/simplified/1/update-zendesk-ticket/"


@pytest.mark.django_db
def test_zendesk_ticket_id_within_case():
    """Test ZendeskTicket.id_within_case"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    first_zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        simplified_case=simplified_case
    )

    assert first_zendesk_ticket.id_within_case == 1

    second_zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        simplified_case=simplified_case
    )

    assert second_zendesk_ticket.id_within_case == 2


@pytest.mark.django_db
def test_case_email_tmplates():
    """Test SimplifiedCase.email_templates returns expected data"""
    email_templates: QuerySet[EmailTemplate] = EmailTemplate.objects.filter(
        is_deleted=False
    )

    assert email_templates.count() == 4
    assertQuerySetEqual(SimplifiedCase().email_templates, email_templates)


@pytest.mark.django_db
def test_case_report_number_of_visits():
    """Test SimplifiedCase.report_number_of_visits returns expected data"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.report_number_of_visits == 0

    ReportVisitsMetrics.objects.create(base_case=simplified_case)
    ReportVisitsMetrics.objects.create(base_case=simplified_case)

    assert simplified_case.report_number_of_visits == 2


@pytest.mark.django_db
def test_case_report_number_of_unique_visitors():
    """Test SimplifiedCase.report_number_of_unique_visitors returns expected data"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.report_number_of_unique_visitors == 0

    ReportVisitsMetrics.objects.create(base_case=simplified_case)
    ReportVisitsMetrics.objects.create(base_case=simplified_case)

    assert simplified_case.report_number_of_unique_visitors == 1


@pytest.mark.django_db
def test_case_website_contact_links_count():
    """Test SimplifiedCase.website_contact_links_count returns expected data"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.website_contact_links_count == 0

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.website_contact_links_count == 0

    Page.objects.create(audit=audit, page_type=Page.Type.CONTACT, url="url")

    assert simplified_case.website_contact_links_count == 1

    Page.objects.create(audit=audit, page_type=Page.Type.STATEMENT, url="url")

    assert simplified_case.website_contact_links_count == 2


def test_case_not_archived():
    """Test that SimplifiedCase.not_archived is true if SimplifiedCase.archived is empty"""
    simplified_case: SimplifiedCase = SimplifiedCase()

    assert simplified_case.not_archived is True

    simplified_case.archive = "archive"

    assert simplified_case.not_archived is False


@pytest.mark.django_db
def test_case_show_start_tests():
    """
    Test that SimplifiedCase.show_start_tests is true when no audit exists and
    the case is not archived
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.show_start_test is True

    simplified_case.archive = "archive"

    assert simplified_case.show_start_test is False

    simplified_case.archive = ""

    assert simplified_case.show_start_test is True

    Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.show_start_test is False


@pytest.mark.django_db
def test_case_not_archived_has_audit():
    """
    Test that SimplifiedCase.not_archived_has_audit is true when audit exists and
    the case is not archived
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.not_archived_has_audit is False

    Audit.objects.create(simplified_case=simplified_case)

    simplified_case: SimplifiedCase = SimplifiedCase.objects.get(id=simplified_case.id)

    assert simplified_case.not_archived_has_audit is True

    simplified_case.archive = "archive"

    assert simplified_case.not_archived_has_audit is False


@pytest.mark.django_db
def test_case_show_create_report_true():
    """Test that SimplifiedCase.show_create_report is true if Case has no report"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.show_create_report is True


@pytest.mark.django_db
def test_case_show_create_report_false():
    """Test that SimplifiedCase.show_create_report is false if Case has a report"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Report.objects.create(base_case=simplified_case)

    assert simplified_case.show_create_report is False


@pytest.mark.django_db
def test_case_not_archived_has_report_true():
    """Test that SimplifiedCase.not_archived_has_report is false if Case has no report"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.not_archived_has_report is False


@pytest.mark.django_db
def test_case_not_archived_has_report_false():
    """Test that SimplifiedCase.not_archived_has_report is true if Case has a report"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Report.objects.create(base_case=simplified_case)

    assert simplified_case.not_archived_has_report is True


@pytest.mark.django_db
def test_show_start_12_week_retest():
    """
    Test SimplifiedCase.show_start_12_week_retest true when Case is not achived,
    has an audit and the retest_date is not set.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.show_start_12_week_retest is False

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.show_start_12_week_retest is True

    audit.retest_date = TODAY

    assert simplified_case.show_start_12_week_retest is False


@pytest.mark.django_db
def test_show_12_week_retest():
    """
    Test SimplifiedCase.show_12_week_retest true when Case is not achived,
    has an audit and the retest_date is set.
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.show_12_week_retest is False

    audit: Audit = Audit.objects.create(simplified_case=simplified_case)

    assert simplified_case.show_12_week_retest is False

    audit.retest_date = TODAY

    assert simplified_case.show_12_week_retest is True


@pytest.mark.django_db
def test_overdue_link_seven_day_no_contact():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and no
    chaser emails have been sent.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.enable_correspondence_process = True
    simplified_case.seven_day_no_contact_email_sent_date = ONE_WEEK_AGO
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "No contact details response overdue"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-request-contact-details", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_no_contact_one_week_chaser():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and only the
    one week chaser email has been sent.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.enable_correspondence_process = True
    simplified_case.seven_day_no_contact_email_sent_date = TWO_WEEKS_AGO
    simplified_case.no_contact_one_week_chaser_due_date = TODAY
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "No contact details response overdue"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-request-contact-details", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_no_contact_four_week_chaser():
    """
    Check overdue link if report is ready to send and seven day no
    contact email sent date is more than seven days ago and only the
    four week chaser email has been sent.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.enable_correspondence_process = True
    simplified_case.seven_day_no_contact_email_sent_date = TWO_WEEKS_AGO
    simplified_case.no_contact_four_week_chaser_due_date = TODAY
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "No contact details response overdue"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-request-contact-details", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_one_week_followup():
    """
    Check overdue link if case is in report correspondence,
    the one week followup is due but not sent.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.report_followup_week_1_due_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.IN_REPORT_CORES
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "1-week follow-up to report due"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-report-one-week-followup", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_four_week_followup():
    """
    Check overdue link if case is in report correspondence,
    the four week followup is due but not sent.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.report_followup_week_4_due_date = ONE_WEEK_AGO
    simplified_case.report_followup_week_1_sent_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.IN_REPORT_CORES
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "4-week follow-up to report due"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-report-four-week-followup", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_report_four_week_followup_sent_one_week_ago():
    """
    Check overdue link if case is in report correspondence,
    the four week followup was sent over a week ago.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.report_followup_week_4_due_date = FOUR_WEEKS_AGO
    simplified_case.report_followup_week_1_sent_date = FOUR_WEEKS_AGO
    simplified_case.report_followup_week_4_sent_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.IN_REPORT_CORES
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert (
        simplified_case.overdue_link.label
        == "4-week follow-up to report sent, case needs to progress"
    )
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-report-acknowledged", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_12_week_deadline_due():
    """
    Check overdue link if case is awaiting 12-week deadline,
    the 12-week due date has passed.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.report_followup_week_12_due_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.AWAITING_12_WEEK_DEADLINE
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "12-week update due"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-12-week-update-requested", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_overdue_link_12_week_correspondence_1_week_chaser_due():
    """
    Check overdue link if case is in 12-week correspondence,
    the 1-week chaser due date has passed.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    simplified_case.twelve_week_1_week_chaser_due_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.AFTER_12_WEEK_CORES
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert simplified_case.overdue_link.label == "1-week follow-up due"
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-12-week-one-week-followup-final",
        kwargs={"pk": simplified_case.id},
    )


@pytest.mark.django_db
def test_overdue_link_12_week_correspondence_1_week_chaser_sent_a_week_ago():
    """
    Check overdue link if case is in 12-week correspondence,
    the 1-week chaser was sent a week ago.
    """
    simplified_case: SimplifiedCase = create_case_for_overdue_link()

    simplified_case.twelve_week_update_requested_date = TWO_WEEKS_AGO
    simplified_case.twelve_week_1_week_chaser_due_date = ONE_WEEK_AGO
    simplified_case.twelve_week_1_week_chaser_sent_date = ONE_WEEK_AGO
    simplified_case.status = SimplifiedCase.Status.AFTER_12_WEEK_CORES
    simplified_case.save()

    assert simplified_case.overdue_link is not None
    assert (
        simplified_case.overdue_link.label
        == "1-week follow-up sent, case needs to progress"
    )
    assert simplified_case.overdue_link.url == reverse(
        "simplified:edit-12-week-update-request-ack", kwargs={"pk": simplified_case.id}
    )


@pytest.mark.django_db
def test_event_history_history_update():
    """Test EventHistory.variables contains expected values for update"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.create(
        simplified_case=simplified_case,
        created_by=user,
        parent=simplified_case,
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.create(
        simplified_case=simplified_case,
        created_by=user,
        parent=simplified_case,
        event_type=SimplifiedEventHistory.Type.CREATE,
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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.create(
        simplified_case=simplified_case,
        created_by=user,
        parent=simplified_case,
        difference=json.dumps({"notes": "Old note -> New note -> separator"}),
    )

    assert event_history.variables == [
        {
            "name": "notes",
            "old_value": "Old note",
            "new_value": "New note -> separator",
        }
    ]


@pytest.mark.django_db
def test_update_case_status():
    """Test SimplifiedCase.update_case_status updates the case status"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(auditor=user)

    assert simplified_case.status == SimplifiedCase.Status.UNASSIGNED

    simplified_case.update_case_status()

    assert simplified_case.status == SimplifiedCase.Status.TEST_IN_PROGRESS


@pytest.mark.parametrize(
    "status, expected_label, expected_url",
    [
        (
            CaseStatus.Status.UNASSIGNED,
            "Go to case metadata",
            "simplified:edit-case-metadata",
        ),
        (
            CaseStatus.Status.TEST_IN_PROGRESS,
            "Go to testing details",
            "simplified:edit-test-results",
        ),
        (
            CaseStatus.Status.REPORT_IN_PROGRESS,
            "Go to report ready for QA",
            "simplified:edit-report-ready-for-qa",
        ),
        (
            CaseStatus.Status.READY_TO_QA,
            "Go to QA approval",
            "simplified:edit-qa-approval",
        ),
        (
            CaseStatus.Status.QA_IN_PROGRESS,
            "Go to QA approval",
            "simplified:edit-qa-approval",
        ),
        (
            CaseStatus.Status.REPORT_READY_TO_SEND,
            "Go to Report sent on",
            "simplified:edit-report-sent-on",
        ),
        (
            CaseStatus.Status.AWAITING_12_WEEK_DEADLINE,
            "Go to 12-week update requested",
            "simplified:edit-12-week-update-requested",
        ),
        (
            CaseStatus.Status.FINAL_DECISION_DUE,
            "Go to closing the case",
            "simplified:edit-case-close",
        ),
        (
            CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND,
            "Go to closing the case",
            "simplified:edit-case-close",
        ),
        (
            CaseStatus.Status.CASE_CLOSED_SENT_TO_ENFORCEMENT_BODY,
            "Go to equality body metadata",
            "simplified:edit-equality-body-metadata",
        ),
        (
            CaseStatus.Status.IN_CORES_WITH_ENFORCEMENT_BODY,
            "Go to equality body metadata",
            "simplified:edit-equality-body-metadata",
        ),
        (
            CaseStatus.Status.COMPLETE,
            "Go to statement enforcement",
            "simplified:edit-statement-enforcement",
        ),
        (
            CaseStatus.Status.DEACTIVATED,
            "Go to case metadata",
            "simplified:edit-case-metadata",
        ),
    ],
)
@pytest.mark.django_db
def test_next_page_link(status, expected_label, expected_url):
    """Check that the expected next page link is returned for each Case status"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(status=status)

    assert simplified_case.next_page_link == Link(
        label=expected_label,
        url=reverse(expected_url, kwargs={"pk": simplified_case.id}),
    )


@pytest.mark.django_db
def test_next_page_link_in_report_cores():
    """
    Check that the expected next page link is returned for Case status in report
    correspondence
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        status=CaseStatus.Status.IN_REPORT_CORES
    )

    assert (
        simplified_case.next_page_link
        == simplified_case.in_report_correspondence_progress
    )


@pytest.mark.django_db
def test_next_page_link_in_12_week_cores():
    """
    Check that the expected next page link is returned for Case status in 12-week
    correspondence
    """
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        status=CaseStatus.Status.AFTER_12_WEEK_CORES
    )

    assert (
        simplified_case.next_page_link
        == simplified_case.twelve_week_correspondence_progress
    )


@pytest.mark.django_db
def test_simplified_case_identifier():
    """Test the SimplifiedCase.case_identifier"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert simplified_case.case_identifier == "#S-1"


def test_simplified_case_report_acknowledged_yes_no():
    """Test the SimplifiedCase.report_acknowledged_yes_no"""

    assert SimplifiedCase().report_acknowledged_yes_no == "No"
    assert (
        SimplifiedCase(
            report_acknowledged_date=datetime(
                2020, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc
            )
        ).report_acknowledged_yes_no
        == "Yes"
    )


@pytest.mark.django_db
def test_equality_body_export_contact_details():
    """Test that contacts fields values are contatenated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Contact.objects.create(
        simplified_case=simplified_case,
        name="Name 1",
        job_title="Job title 1",
        email="email1",
    )
    Contact.objects.create(
        simplified_case=simplified_case,
        name="Name 2",
        job_title="Job title 2",
        email="email2",
    )

    assert (
        simplified_case.equality_body_export_contact_details
        == """Name 2
Job title 2
email2

Name 1
Job title 1
email1
"""
    )


@pytest.mark.django_db
def test_manage_contacts_url():
    """Test SimplifiedCase.manage_contacts_url is working"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        simplified_case.manage_contacts_url == "/simplified/1/manage-contact-details/"
    )


@pytest.mark.django_db
def test_email_template_list_url():
    """Test SimplifiedCase.email_template_list_url is working"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        simplified_case.email_template_list_url == "/simplified/1/email-template-list/"
    )


@pytest.mark.django_db
def test_email_template_preview_url_name():
    """Test SimplifiedCase.email_template_preview_url_name is working"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()

    assert (
        simplified_case.email_template_preview_url_name
        == "simplified:email-template-preview"
    )


def test_target_of_test():
    """Test SimplifiedCase.target_of_test"""
    assert SimplifiedCase().target_of_test == "website"


@pytest.mark.django_db
def test_simplified_history_get_absolute_url():
    """Test SimplifiedCaseHistory.get_absolute_url"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    simplified_case_history: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.STATUS,
            created_by=user,
        )
    )

    assert simplified_case_history.get_absolute_url() == reverse(
        "simplified:edit-case-note", kwargs={"pk": simplified_case_history.id}
    )


@pytest.mark.django_db
def test_simplified_case_case_history_undeleted():
    """Test SimplifiedCase.case_history returns only undeleted events"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    simplified_case_history_status: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.STATUS,
            created_by=user,
        )
    )
    simplified_case_history_note: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.NOTE,
            created_by=user,
            is_deleted=True,
        )
    )

    assert simplified_case_history_status in simplified_case.case_history()
    assert simplified_case_history_note not in simplified_case.case_history()


@pytest.mark.django_db
def test_simplified_case_notes_history_relevant():
    """Test SimplifiedCase.notes_history returns only relevant events"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    simplified_case_history_status: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.STATUS,
            created_by=user,
        )
    )
    simplified_case_history_note: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    assert simplified_case_history_status not in simplified_case.notes_history()
    assert simplified_case_history_note in simplified_case.notes_history()


@pytest.mark.django_db
def test_simplified_case_most_recent_case_note():
    """Test SimplifiedCase.most_recent_case_note returns the most recent note"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    user: User = User.objects.create()
    SimplifiedCaseHistory.objects.create(
        simplified_case=simplified_case,
        event_type=SimplifiedCaseHistory.EventType.NOTE,
        created_by=user,
    )
    simplified_case_history_last: SimplifiedCaseHistory = (
        SimplifiedCaseHistory.objects.create(
            simplified_case=simplified_case,
            event_type=SimplifiedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    assert simplified_case.most_recent_case_note == simplified_case_history_last
