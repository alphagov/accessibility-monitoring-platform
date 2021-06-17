"""
Tests for cases views
"""
import pytest

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from ..forms import CaseSearchForm
from ..models import Case, Contact
from ..views import CaseListView


@pytest.mark.django_db
def test_case_detail_view(admin_client):
    """ Test that the case detail view page loads """
    case: Case = Case.objects.create()
    response: HttpResponse = admin_client.get(
        reverse("cases:case-detail", kwargs={"pk": case.id})
    )
    assert response.status_code == 200
    assert (
        bytes(f'<h1 class="govuk-heading-xl">View case #{case.id}</h1>', "utf-8")
        in response.content
    )


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
    assert b"Unarchived Contact" in response.content
    assert b"Archived Contact" not in response.content


@pytest.mark.django_db
def test_case_list_view(admin_client):
    """ Test that the case list view page loads """
    response: HttpResponse = admin_client.get(reverse("cases:case-list"))
    assert response.status_code == 200
    assert b'<h1 class="govuk-heading-xl">Cases and reports</h1>' in response.content
