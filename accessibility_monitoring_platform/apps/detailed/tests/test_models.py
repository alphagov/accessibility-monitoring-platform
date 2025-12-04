"""
Tests for detailed models
"""

from datetime import date

import pytest
from django.contrib.auth.models import User

from ...common.models import Boolean
from ...simplified.models import SimplifiedCase
from ..models import Contact, DetailedCase, DetailedCaseHistory, ZendeskTicket

ORGANISATION_NAME: str = "Organisation Name"
WEBSITE_NAME: str = "Website Name"
EXPECTED_FORMATTED_CONTACTS: str = """Name 2
Job title 2
email2
Information 2

Name 1
Job title 1
email1
Information 1
"""


@pytest.mark.django_db
def test_detailed_case_identifier():
    """Test DetailedCase.case_identifier"""
    detailed_case: DetailedCase = DetailedCase.objects.create()

    assert detailed_case.case_identifier == "#D-1"


@pytest.mark.django_db
def test_detailed_case_title():
    """Test DetailedCase.title"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )

    assert detailed_case.title == f"{ORGANISATION_NAME} &nbsp;|&nbsp; #D-1"

    detailed_case.website_name = WEBSITE_NAME
    detailed_case.save()

    assert (
        detailed_case.title
        == f"{WEBSITE_NAME} &nbsp;|&nbsp; {ORGANISATION_NAME} &nbsp;|&nbsp; #D-1"
    )


@pytest.mark.django_db
def test_detailed_case_status_history():
    """Test DetailedCase.status_history returns only relevant events"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    detailed_case_history_status: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.STATUS,
            created_by=user,
        )
    )
    detailed_case_history_note: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    assert detailed_case_history_status in detailed_case.status_history()
    assert detailed_case_history_note not in detailed_case.status_history()


@pytest.mark.django_db
def test_detailed_case_notes_history():
    """Test DetailedCase.notes_history returns only relevant events"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    detailed_case_history_status: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.STATUS,
            created_by=user,
        )
    )
    detailed_case_history_note: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    assert detailed_case_history_status not in detailed_case.notes_history()
    assert detailed_case_history_note in detailed_case.notes_history()


@pytest.mark.django_db
def test_detailed_case_most_recent_history():
    """Test DetailedCase.most_recent_history returns the most recent event"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=DetailedCaseHistory.EventType.NOTE,
        created_by=user,
    )
    detailed_case_history_last: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    assert detailed_case.most_recent_history == detailed_case_history_last


@pytest.mark.django_db
def test_detailed_case_contacts():
    """Test DetailedCase.contacts returns the contacts"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    contact: Contact = Contact.objects.create(
        detailed_case=detailed_case, created_by=user
    )

    assert list(detailed_case.contacts) == [contact]


@pytest.mark.django_db
def test_detailed_case_preferred_contacts():
    """Test DetailedCase.preferred_contacts returns the preferred contacts"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    Contact.objects.create(detailed_case=detailed_case, created_by=user)
    preferred_contact: Contact = Contact.objects.create(
        detailed_case=detailed_case, created_by=user, preferred=Contact.Preferred.YES
    )

    assert list(detailed_case.preferred_contacts) == [preferred_contact]


@pytest.mark.django_db
def test_detailed_case_history_saves_detailed_case_status():
    """Test DetailedCaseiHistory saves the current DetailedCase status"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        status=DetailedCase.Status.REVIEWING_CHANGES
    )
    user: User = User.objects.create()
    detailed_case_history: DetailedCaseHistory = DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=DetailedCaseHistory.EventType.NOTE,
        created_by=user,
    )

    assert (
        detailed_case_history.detailed_case_status
        == DetailedCase.Status.REVIEWING_CHANGES
    )


def test_contact_str():
    """Test Contact.__str__()"""
    contact: Contact = Contact(name="Contact Name", contact_details="name@example.com")

    assert str(contact) == "Contact Name name@example.com"


@pytest.mark.django_db
def test_zendesk_id_within_case():
    """
    Test that ZendeskTicket.id_within_case is set to number of Zendesk tickets in case
    or id from Zendesk URL
    """
    detailed_case: DetailedCase = DetailedCase.objects.create()
    zendesk_ticket: ZendeskTicket = ZendeskTicket.objects.create(
        detailed_case=detailed_case, url="https://non-zendesk-url"
    )

    assert zendesk_ticket.id_within_case == 1

    zendesk_ticket.url = "https://govuk.zendesk.com/agent/tickets/1234567"
    zendesk_ticket.save()

    assert zendesk_ticket.id_within_case == 1234567


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

    detailed_case: DetailedCase = DetailedCase.objects.create(
        previous_case_url=previous_case_url
    )

    assert detailed_case.previous_case_identifier == previous_case_identifier


@pytest.mark.django_db
def test_detailed_case_equality_body_export_contact_details():
    """Test that contacts fields values are contatenated"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    Contact.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        name="Name 1",
        job_title="Job title 1",
        contact_details="email1",
        information="Information 1",
    ),
    Contact.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        name="Name 2",
        job_title="Job title 2",
        contact_details="email2",
        information="Information 2",
    ),

    assert (
        detailed_case.equality_body_export_contact_details
        == EXPECTED_FORMATTED_CONTACTS
    )


def test_detailed_case_report_acknowledged_yes_no():
    """Test the DetailedCase.report_acknowledged_yes_no"""

    assert DetailedCase().report_acknowledged_yes_no == "No"
    assert (
        DetailedCase(
            report_acknowledged_date=date(2020, 1, 1)
        ).report_acknowledged_yes_no
        == "Yes"
    )
    assert (
        DetailedCase(
            report_acknowledged_date=date(2020, 1, 1),
            no_psb_contact=Boolean.YES,
        ).report_acknowledged_yes_no
        == "No"
    )


def test_detailed_case_number_of_issues_fixed():
    """Test the DetailedCase.number_of_issues_fixed"""

    assert DetailedCase().number_of_issues_fixed is None
    assert (
        DetailedCase(initial_total_number_of_issues=50).number_of_issues_fixed is None
    )
    assert (
        DetailedCase(
            initial_total_number_of_issues=50, retest_total_number_of_issues=20
        ).number_of_issues_fixed
        == 30
    )
    assert (
        DetailedCase(
            initial_total_number_of_issues=50, retest_total_number_of_issues=60
        ).number_of_issues_fixed
        == -10
    )


def test_detailed_case_percentage_of_issues_fixed():
    """Test the DetailedCase.percentage_of_issues_fixed"""

    assert DetailedCase().percentage_of_issues_fixed is None
    assert (
        DetailedCase(initial_total_number_of_issues=50).percentage_of_issues_fixed
        is None
    )
    assert (
        DetailedCase(
            initial_total_number_of_issues=50, retest_total_number_of_issues=20
        ).percentage_of_issues_fixed
        == 60
    )
    assert (
        DetailedCase(
            initial_total_number_of_issues=50, retest_total_number_of_issues=60
        ).percentage_of_issues_fixed
        == -20
    )
    assert (
        DetailedCase(
            initial_total_number_of_issues=50, retest_total_number_of_issues=0
        ).percentage_of_issues_fixed
        == 100
    )


def test_detailed_case_equality_body_export_statement_found_at_retest():
    """Test the DetailedCase.equality_body_export_statement_found_at_retest"""

    assert DetailedCase().equality_body_export_statement_found_at_retest == "No"
    assert (
        DetailedCase(
            retest_statement_compliance_state=DetailedCase.StatementCompliance.COMPLIANT
        ).equality_body_export_statement_found_at_retest
        == "Yes"
    )
    assert (
        DetailedCase(
            retest_statement_compliance_state=DetailedCase.StatementCompliance.NOT_COMPLIANT
        ).equality_body_export_statement_found_at_retest
        == "Yes"
    )
    assert (
        DetailedCase(
            retest_statement_compliance_state=DetailedCase.StatementCompliance.NO_STATEMENT
        ).equality_body_export_statement_found_at_retest
        == "No"
    )
    assert (
        DetailedCase(
            retest_statement_compliance_state=DetailedCase.StatementCompliance.UNKNOWN
        ).equality_body_export_statement_found_at_retest
        == "No"
    )
