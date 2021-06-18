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


@pytest.mark.django_db
def test_case_detail_view(admin_client):
    """ Test that the case detail view page loads """
    case: Case = Case.objects.create()

    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id})
    )

    assert response.status_code == 200
    assertContains(response, f'<h1 class="govuk-heading-xl">View case #{case.id}</h1>')


@pytest.mark.django_db
def test_case_detail_view_leaves_out_archived_contact(admin_client):
    """ Test that archived Contacts are not included in context """
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
def test_case_list_view(admin_client):
    """ Test that the case list view page loads """
    response: HttpResponse = admin_client.get(reverse("cases:case-list"))

    assert response.status_code == 200
    assertContains(response, '<h1 class="govuk-heading-xl">Cases and reports</h1>')


@pytest.mark.django_db
def test_case_list_view_leaves_out_archived_case(admin_client):
    """ Test that the case list view page does not include archived cases """
    Case.objects.create(organisation_name="Not Archived")
    Case.objects.create(organisation_name="Is Archived", is_archived=True)

    response: HttpResponse = admin_client.get(reverse("cases:case-list"))

    assert response.status_code == 200
    assertContains(response, '<h2 class="govuk-heading-m">1 cases found</h2>')
    assertContains(response, "Not Archived")
    assertNotContains(response, "Is Archived")


@pytest.mark.django_db
def test_case_list_view_filters_by_case_number(admin_client):
    """ Test that the case list view page can be filtered by case number """
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
    """ Test that the case list view page can be filtered by string """
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
    """ Test that the case list view page can be filtered by user """
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


@pytest.mark.django_db
def test_case_list_view_date_range_filters(admin_client):
    """ Test that the case list view page can be filtered by date range """
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
