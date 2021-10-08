"""
Test urls of cases app
"""

import pytest
from pytest_django.asserts import assertContains

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.urls import reverse

from ...cases.models import Case
from ...users.models import Auditor

ORGANISATION_NAME: str = "Organisation name two"
USER_FIRST_NAME: str = "Userone"


@pytest.mark.parametrize(
    "url, page_title",
    [
        (reverse("cases:case-list"), "Search"),
        (reverse("cases:case-create"), "Create case"),
        (reverse("contact-admin"), "Contact admin"),
        (reverse("issue-report"), "Report an issue"),
    ],
)
def test_page_title_present(url, page_title, admin_client):
    """Check page header and title are set"""
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertContains(response, f"<title>{page_title}</title>")
    assertContains(response, f'<h1 class="govuk-heading-xl">{page_title}</h1>')


@pytest.mark.django_db
def test_page_title_and_heading_for_case_page(admin_client):
    """Page title and heading for case page present"""
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    url: str = reverse("cases:case-detail", kwargs={"pk": case.id})
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertContains(response, f"<title>{ORGANISATION_NAME} | View case</title>")
    assertContains(
        response,
        '<h1 class="govuk-heading-xl" style="margin-bottom:15px; padding-right: 20px;">View case</h1>',
    )


@pytest.mark.django_db
def test_top_menu_form_present(admin_client):
    """Test search field present"""
    response: HttpResponse = admin_client.get("/")

    assert response.status_code == 200
    assertContains(
        response,
        '<input type="text" name="search" class="govuk-input govuk-input--width-10" placeholder="Search" maxlength="100" id="id_search">',
    )


@pytest.mark.django_db
def test_active_qa_auditor_present(admin_client):
    """Test active QA auditor present"""
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    Auditor.objects.create(user=user, active_qa_auditor=True)
    response: HttpResponse = admin_client.get("/")

    assert response.status_code == 200
    assertContains(
        response,
        f"""<div class="govuk-heading-xl no-bottom-margin">{USER_FIRST_NAME}</div>""",
        html=True,
    )
