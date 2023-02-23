"""
Tests for cases models
"""
import pytest
from datetime import date, datetime, timedelta
from typing import List

from ..models import Case, Contact
from ...comments.models import Comment

DOMAIN: str = "example.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}/index.html"
ORGANISATION_NAME: str = "Organisation name"


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


def test_next_action_due_date_for_in_report_correspondence():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in report correspondence.
    """
    any_old_date: date = date(2020, 4, 1)
    report_followup_week_1_due_date: date = date(2020, 1, 1)
    report_followup_week_4_due_date: date = date(2020, 1, 4)
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case(
        status="in-report-correspondence",
        report_followup_week_1_sent_date=any_old_date,
        report_followup_week_4_sent_date=any_old_date,
        report_followup_week_1_due_date=report_followup_week_1_due_date,
        report_followup_week_4_due_date=report_followup_week_4_due_date,
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )

    case.report_followup_week_4_sent_date = None
    assert case.next_action_due_date == report_followup_week_4_due_date

    case.report_followup_week_1_sent_date = None
    assert case.next_action_due_date == report_followup_week_1_due_date


def test_next_action_due_date_for_in_probation_period():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in probation period.
    """
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case(
        status="in-probation-period",
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )
    assert case.next_action_due_date == report_followup_week_12_due_date


def test_next_action_due_date_for_in_12_week_correspondence():
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in 12-week correspondence.
    """
    twelve_week_1_week_chaser_due_date: date = date(2020, 1, 1)

    case: Case = Case(
        status="in-12-week-correspondence",
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
    )

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
def test_next_action_due_date_not_set(status):
    """
    Check that the next_action_due_date is correctly calculated
    when case status is in probation period.
    """
    twelve_week_1_week_chaser_due_date: date = date(2020, 1, 1)
    report_followup_week_12_due_date: date = date(2020, 1, 12)

    case: Case = Case(
        status=status,
        report_followup_week_12_due_date=report_followup_week_12_due_date,
        twelve_week_1_week_chaser_due_date=twelve_week_1_week_chaser_due_date,
    )
    assert case.next_action_due_date == date(1970, 1, 1)


@pytest.mark.parametrize(
    "report_followup_week_12_due_date, expected_tense",
    [
        (date.today() - timedelta(days=1), "past"),
        (date.today(), "present"),
        (date.today() + timedelta(days=1), "future"),
    ],
)
def test_next_action_due_date_tense(report_followup_week_12_due_date, expected_tense):
    """Check that the calculated next_action_due_date is correctly reported"""
    case: Case = Case(
        status="in-probation-period",
        report_followup_week_12_due_date=report_followup_week_12_due_date,
    )
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
