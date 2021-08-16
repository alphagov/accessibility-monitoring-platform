"""
Tests for cases models
"""
import pytest
from datetime import date, datetime

from ..models import Case, Contact

DOMAIN = "example.com"
HOME_PAGE_URL = f"https://{DOMAIN}/index.html"
ORGANISATION_NAME = "Organisation name"


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
    case.organisation_name: str = updated_organisation_name
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

    assert case.completed is None

    case.case_completed: str = "no-action"
    case.save()
    updated_case: Case = Case.objects.get(pk=case.id)

    assert updated_case.completed is not None
    assert isinstance(updated_case.completed, datetime)


@pytest.mark.django_db
def test_contact_name_is_as_expected():
    """Test that name is a combination of first_name and last_name"""
    case: Case = Case.objects.create()
    contact: Contact = Contact.objects.create(
        case=case,
        first_name="Joe",
        last_name="Bloggs",
    )

    assert contact.name == "Joe Bloggs"


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
    updated_first_name: str = "updated first name"
    contact.first_name: str = updated_first_name
    contact.save()
    updated_contact: Contact = Contact.objects.get(pk=contact.id)

    assert updated_contact.first_name == updated_first_name
    assert updated_contact.created == original_created_timestamp


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
        ("https://www3.halton.gov.uk/Pages/Home.aspx", "www3.halton.gov.uk/Pages/…"),
    ],
)
def test_formatted_home_page_url(url, expected_formatted_url):
    case: Case = Case(home_page_url=url)
    assert case.formatted_home_page_url == expected_formatted_url
