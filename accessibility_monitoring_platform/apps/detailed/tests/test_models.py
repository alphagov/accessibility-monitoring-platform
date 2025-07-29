"""
Tests for detailed models
"""

import pytest
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from ..models import Contact, DetailedCase, DetailedCaseHistory

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
@pytest.mark.parametrize(
    "history_type, detailed_case_history_attr",
    [
        (DetailedCaseHistory.EventType.STATUS, "status_history"),
        (DetailedCaseHistory.EventType.CONTACT_NOTE, "contact_notes_history"),
        (DetailedCaseHistory.EventType.RECOMMENDATION, "recommendation_history"),
        (
            DetailedCaseHistory.EventType.UNRESPONSIVE_NOTE,
            "unresponsive_psb_notes_history",
        ),
    ],
)
def test_detailed_case_histories(history_type, detailed_case_history_attr):
    """Test DetailedCase histories return only relevant events"""
    detailed_case: DetailedCase = DetailedCase.objects.create()
    user: User = User.objects.create()
    detailed_case_history_included: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=history_type,
            created_by=user,
        )
    )
    detailed_case_history_excluded: DetailedCaseHistory = (
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.NOTE,
            created_by=user,
        )
    )

    detailed_case_history: QuerySet[DetailedCaseHistory] = getattr(
        detailed_case, detailed_case_history_attr
    )()

    assert detailed_case_history_included in detailed_case_history
    assert detailed_case_history_excluded not in detailed_case_history


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
    contact: Contact = Contact(name="Contact Name", contact_point="name@example.com")

    assert str(contact) == "Contact Name name@example.com"
