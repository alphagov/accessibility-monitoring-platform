"""
Tests for detailed models
"""

import pytest
from django.contrib.auth.models import User

from ..models import Contact, DetailedCase, DetailedCaseHistory, ZendeskTicket

ORGANISATION_NAME: str = "Organisation Name"
WEBSITE_NAME: str = "Website Name"


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
