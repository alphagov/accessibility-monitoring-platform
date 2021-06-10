"""
Tests for cases views
"""
import pytest

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

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
        archived=True,
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


@pytest.mark.parametrize(
    "url_param,sql_clause",
    [
        ("case_number=42", '"cases_case"."id" = 42'),
        (
            "domain=domain+name",
            'UPPER("cases_case"."domain"::text) LIKE UPPER(%domain name%))',
        ),
        (
            "organisation=Organisation+Name",
            'UPPER("cases_case"."organisation_name"::text) LIKE UPPER(%Organisation Name%))',
        ),
        ("auditor=Paul+Ahern", '"cases_case"."auditor" = Paul Ahern'),
        ("status=new-case", '"cases_case"."status" = new-case'),
        (
            "start_date_0=1&start_date_1=1&start_date_2=1800",
            '"cases_case"."created" >= 1800-01-01 00:00:00+00:00',
        ),
        (
            "end_date_0=1&end_date_1=1&end_date_2=2200",
            '"cases_case"."created" <= 2200-01-01 00:00:00+00:00',
        ),
    ],
)
def test_case_list_view_applies_filters_to_queryset(url_param, sql_clause, rf):
    """ Test that filters in the url parameters are applied in the sql """
    request: HttpRequest = rf.get(f"{reverse('cases:case-list')}?{url_param}")
    view: CaseListView = CaseListView()
    view.request = request

    queryset: QuerySet = view.get_queryset()

    assert sql_clause in str(queryset.query)
