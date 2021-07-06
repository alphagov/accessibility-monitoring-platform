"""
Tests for cases views
"""
from datetime import datetime
import pytest
import pytz

from pytest_django.asserts import assertContains, assertNotContains

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

from ..models import Case, Contact
from ..views import CASE_FIELDS_TO_EXPORT

CASE_FIELDS_TO_EXPORT_STR = ",".join(CASE_FIELDS_TO_EXPORT)


@pytest.mark.django_db
def test_case_detail_view_leaves_out_archived_contact(admin_client):
    """Test that archived Contacts are not included in context"""
    case: Case = Case.objects.create()
    unarchived_contact: Contact = Contact.objects.create(
        case=case,
        first_name="Unarchived",
        last_name="Contact",
    )
    Contact.objects.create(
        case=case,
        first_name="Archived",
        last_name="Contact",
        is_archived=True,
    )

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assert set(response.context["contacts"]) == set([unarchived_contact])
    assertContains(response, "Unarchived Contact")
    assertNotContains(response, "Archived Contact")


@pytest.mark.django_db
def test_case_list_view_leaves_out_archived_case(admin_client):
    """Test that the case list view page does not include archived cases"""
    Case.objects.create(organisation_name="Not Archived")
    Case.objects.create(organisation_name="Is Archived", is_archived=True)

    response: HttpResponse = admin_client.get(reverse("cases:case-list"))

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Not Archived")
    assertNotContains(response, "Is Archived")


@pytest.mark.django_db
def test_case_list_view_filters_by_case_number(admin_client):
    """Test that the case list view page can be filtered by case number"""
    included_case: Case = Case.objects.create(organisation_name="Included")
    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?case_number={included_case.id}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,value,url_parameter_name",
    [
        ("domain", "included.com", "domain"),
        ("organisation_name", "IncludedOrg", "organisation"),
        ("status", "complete", "status"),
    ],
)
@pytest.mark.django_db
def test_case_list_view_string_filters(
    field_name, value, url_parameter_name, admin_client
):
    """Test that the case list view page can be filtered by string"""
    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(included_case, field_name, value)
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}={value}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,url_parameter_name",
    [
        ("auditor", "auditor"),
        ("reviewer", "reviewer"),
    ],
)
@pytest.mark.django_db
def test_case_list_view_user_filters(field_name, url_parameter_name, admin_client):
    """Test that the case list view page can be filtered by user"""
    user = User.objects.create()
    included_case: Case = Case.objects.create(organisation_name="Included")
    setattr(included_case, field_name, user)
    included_case.save()

    Case.objects.create(organisation_name="Excluded")

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}={user.id}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.parametrize(
    "field_name,url_parameter_name",
    [
        ("auditor", "auditor"),
        ("reviewer", "reviewer"),
    ],
)
@pytest.mark.django_db
def test_case_list_view_user_unassigned_filters(
    field_name, url_parameter_name, admin_client
):
    """Test that the case list view page can be filtered by unassigned user values"""
    Case.objects.create(organisation_name="Included")

    user = User.objects.create()
    excluded_case: Case = Case.objects.create(organisation_name="Excluded")
    setattr(excluded_case, field_name, user)
    excluded_case.save()

    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameter_name}=none"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.django_db
def test_case_list_view_date_range_filters(admin_client):
    """Test that the case list view page can be filtered by date range"""
    included_created_date: datetime = datetime(
        year=2021, month=6, day=5, tzinfo=pytz.UTC
    )
    excluded_created_date: datetime = datetime(
        year=2021, month=5, day=5, tzinfo=pytz.UTC
    )
    Case.objects.create(organisation_name="Included", created=included_created_date)
    Case.objects.create(organisation_name="Excluded", created=excluded_created_date)

    url_parameters = "start_date_0=1&start_date_1=6&start_date_2=2021&end_date_0=10&end_date_1=6&end_date_2=2021"
    response: HttpResponse = admin_client.get(
        f"{reverse('cases:case-list')}?{url_parameters}"
    )

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Included")
    assertNotContains(response, "Excluded")


@pytest.mark.django_db
def test_case_export_list_view(admin_client):
    """Test that the case export list view returns csv data"""
    response: HttpResponse = admin_client.get(reverse("cases:case-export-list"))

    assert response.status_code == 200
    assertContains(response, CASE_FIELDS_TO_EXPORT_STR)


@pytest.mark.django_db
def test_case_export_single_view(admin_client):
    """Test that the case export single view returns csv data"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-export-single", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, CASE_FIELDS_TO_EXPORT_STR)


@pytest.mark.django_db
def test_archive_case_view(admin_client):
    """Test that archive case view archives case"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:archive-case", kwargs={"pk": case.id})
    )

    assert response.status_code == 302
    assert response.url == reverse("cases:case-list")

    case_from_db: Case = Case.objects.get(pk=case.id)

    assert case_from_db.is_archived


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("cases:case-list", '<h1 class="govuk-heading-xl">Cases and reports</h1>'),
        ("cases:case-export-list", CASE_FIELDS_TO_EXPORT_STR),
        ("cases:case-create", '<h1 class="govuk-heading-xl">Create case</h1>'),
    ],
)
@pytest.mark.django_db
def test_non_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the non-case-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        ("cases:case-export-single", CASE_FIELDS_TO_EXPORT_STR),
        ("cases:case-detail", '<h1 class="govuk-heading-xl">View case #'),
        ("cases:edit-case-details", "<li>Case details</li>"),
        ("cases:edit-contact-details", "<li>Contact details</li>"),
        ("cases:edit-test-results", "<li>Testing details</li>"),
        ("cases:edit-report-details", "<li>Report details</li>"),
        ("cases:edit-post-report-details", "<li>Post report</li>"),
    ],
)
@pytest.mark.django_db
def test_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the case-specific view page loads"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse(path_name, kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, expected_content)


@pytest.mark.parametrize(
    "button_name, expected_redirect_path",
    [
        ("save_continue", "cases:edit-contact-details"),
        ("save_exit", "cases:case-detail"),
    ],
)
@pytest.mark.django_db
def test_create_case_redirects_based_on_button_pressed(
    button_name, expected_redirect_path, admin_client
):
    """Test that a successful case create redirects based on the button pressed"""
    response: HttpResponse = admin_client.post(
        reverse("cases:case-create"),
        {
            "home_page_url": "https://domain.com",
            button_name: "Button value",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse(expected_redirect_path, kwargs={"pk": 1})


@pytest.mark.parametrize(
    "case_edit_path, button_name, expected_redirect_path",
    [
        ("cases:edit-case-details", "save_continue", "cases:edit-contact-details"),
        ("cases:edit-case-details", "save_exit", "cases:case-detail"),
        ("cases:edit-contact-details", "save_continue", "cases:edit-test-results"),
        ("cases:edit-contact-details", "save_exit", "cases:case-detail"),
        ("cases:edit-test-results", "save_continue", "cases:edit-report-details"),
        ("cases:edit-test-results", "save_exit", "cases:case-detail"),
        (
            "cases:edit-report-details",
            "save_continue",
            "cases:edit-post-report-details",
        ),
        ("cases:edit-report-details", "save_exit", "cases:case-detail"),
        ("cases:edit-post-report-details", "save_exit", "cases:case-detail"),
    ],
)
@pytest.mark.django_db
def test_case_edit_redirects_based_on_button_pressed(
    case_edit_path, button_name, expected_redirect_path, admin_client
):
    """Test that a successful case update redirects based on the button pressed"""
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.post(
        reverse(case_edit_path, kwargs={"pk": case.id}),
        {
            "home_page_url": "https://domain.com",
            button_name: "Button value",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse(expected_redirect_path, kwargs={"pk": case.id})


@pytest.mark.django_db
def test_preferred_contact_not_displayed(admin_client):
    """
    Test that the preferred contact field is not displayed when there is only one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertNotContains(response, "Preferred contact?")


@pytest.mark.django_db
def test_preferred_contact_displayed(admin_client):
    """
    Test that the preferred contact field is displayed when there is more than one contact
    """
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)
    Contact.objects.create(case=case)

    response: HttpResponse = admin_client.get(
        reverse("cases:edit-contact-details", kwargs={"pk": case.id}),
    )
    assert response.status_code == 200
    assertContains(response, "Preferred contact?")
