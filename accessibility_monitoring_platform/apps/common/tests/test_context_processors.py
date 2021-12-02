"""
Test context processor of common app
"""
import pytest
from pytest_django.asserts import assertContains

from typing import Dict, Union

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.urls import reverse

from ..context_processors import platform_page
from ..forms import AMPTopMenuForm
from ...cases.models import Case
from ...common.models import Platform
from ...common.utils import get_platform_settings

ORGANISATION_NAME: str = "Organisation name two"
USER_FIRST_NAME: str = "Userone"


class MockRequest:
    def __init__(self, path: str, absolute_uri: str, user: User):
        self.path = path
        self.absolute_uri = absolute_uri
        self.user = user

    def build_absolute_uri(self):
        return self.absolute_uri


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
    url: str = reverse("cases:case-detail", kwargs={"pk": case.id})  # type: ignore
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
        '<input type="text" name="search" class="govuk-input govuk-input--width-10"'
        ' placeholder="Search" maxlength="100" id="id_search">',
    )


@pytest.mark.django_db
def test_active_qa_auditor_present(admin_client):
    """Test active QA auditor present"""
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    platform: Platform = get_platform_settings()
    platform.active_qa_auditor = user
    platform.save()

    response: HttpResponse = admin_client.get("/")

    assert response.status_code == 200
    assertContains(
        response,
        f"""<div class="govuk-heading-xl no-bottom-margin">{USER_FIRST_NAME}</div>""",
        html=True,
    )


@pytest.mark.django_db
def test_platform_page_template_context():
    """
    Check number of reminders for user, prototype name and
    platform settings added to context.
    """
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    mock_request = MockRequest(
        path="/",
        absolute_uri="https://prototype-name.london.cloudapps.digital/",
        user=user,
    )
    platform_page_context: Dict[
        str, Union[AMPTopMenuForm, str, Platform, int]
    ] = platform_page(mock_request)

    assert platform_page_context["prototype_name"] == "prototype-name"
    assert platform_page_context["platform"] is not None
    assert platform_page_context["number_of_reminders"] == 0
