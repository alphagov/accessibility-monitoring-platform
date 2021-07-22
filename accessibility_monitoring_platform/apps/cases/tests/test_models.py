"""
Tests for cases models
"""
import pytest
from datetime import datetime

from ..models import Case, Contact

DOMAIN = "example.com"
HOME_PAGE_URL = f"https://{DOMAIN}/index.html"
ORGANISATION_NAME = "Organisation name"


@pytest.mark.django_db
def test_case_created_timestamp_is_populated():
    """Test the Case created field is populated the first time the Case is saved"""
    case = Case.objects.create()

    assert case.created is not None
    assert isinstance(case.created, datetime)


@pytest.mark.django_db
def test_case_created_timestamp_is_not_updated():
    """Test the Case created field is not updated on subsequent saves"""
    case = Case.objects.create()

    original_created_timestamp = case.created
    updated_organisation_name = "updated organisation name"
    case.organisation_name = updated_organisation_name
    case.save()
    updated_case = Case.objects.get(pk=case.id)

    assert updated_case.organisation_name == updated_organisation_name
    assert updated_case.created == original_created_timestamp


@pytest.mark.django_db
def test_case_domain_is_populated_from_home_page_url():
    """Test the Case domain field is populated from the home_page_url"""
    case = Case.objects.create(home_page_url=HOME_PAGE_URL)

    assert case.domain == DOMAIN


@pytest.mark.django_db
def test_case_renders_as_id_bar_organisation_name():
    """Test the Case string is id | organisation_name"""
    case = Case.objects.create(organisation_name=ORGANISATION_NAME)

    assert str(case) == f"#{case.id} | {case.organisation_name}"


@pytest.mark.django_db
def test_case_summary_is_id_bar_organisation_name_bar_domain():
    """Test the Case summary string is id | organisation_name | domain"""
    case = Case.objects.create(
        home_page_url=HOME_PAGE_URL, organisation_name=ORGANISATION_NAME
    )

    assert case.summary == f"{case.organisation_name} | {case.domain} | #{case.id}"


@pytest.mark.django_db
def test_case_completed_timestamp_is_updated_on_completion():
    """Test the Case completed date field is updated when case_completed is set"""
    case = Case.objects.create()

    assert case.completed is None

    case.case_completed = "no-action"
    case.save()
    updated_case = Case.objects.get(pk=case.id)

    assert updated_case.completed is not None
    assert isinstance(updated_case.completed, datetime)


@pytest.mark.django_db
def test_contact_name_is_as_expected():
    """Test that name is a combination of first_name and last_name"""
    case = Case.objects.create()
    contact = Contact.objects.create(
        case=case,
        first_name="Joe",
        last_name="Bloggs",
    )

    assert contact.name == "Joe Bloggs"


@pytest.mark.django_db
def test_contact_created_timestamp_is_populated():
    """Test the created field is populated the first time the Contact is saved"""
    case = Case.objects.create()
    contact = Contact.objects.create(case=case)

    assert contact.created is not None
    assert isinstance(contact.created, datetime)


@pytest.mark.django_db
def test_contact_created_timestamp_is_not_updated():
    """Test the created field is not updated on subsequent save"""
    case = Case.objects.create()
    contact = Contact.objects.create(case=case)

    original_created_timestamp = contact.created
    updated_first_name = "updated first name"
    contact.first_name = updated_first_name
    contact.save()
    updated_contact = Contact.objects.get(pk=contact.id)

    assert updated_contact.first_name == updated_first_name
    assert updated_contact.created == original_created_timestamp
