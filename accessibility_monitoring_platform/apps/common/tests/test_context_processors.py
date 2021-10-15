"""
Test urls of cases app
"""
import pytest
from pytest_django.asserts import assertContains

from typing import Dict, Union

from django.http.response import HttpResponse
from django.urls import reverse

from ..context_processors import platform_page
from ..forms import AMPTopMenuForm
from ...cases.models import Case

ORGANISATION_NAME: str = "Organisation name two"


class MockRequest:
    def __init__(self, path: str, absolute_uri: str):
        self.path = path
        self.absolute_uri = absolute_uri

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
    case: Case = Case.objects.create(organisation_name=ORGANISATION_NAME)
    url: str = reverse("cases:case-detail", kwargs={"pk": case.id})
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertContains(response, f"<title>{ORGANISATION_NAME} | View case</title>")
    assertContains(
        response,
        '<h1 class="govuk-heading-xl" style="margin-bottom:15px; padding-right: 20px;">View case</h1>',
    )


def test_platform_page_returns_prototype_and_page_names():
    """Check prototype name, page heading and title added to context"""
    mock_request = MockRequest(
        path="/", absolute_uri="https://prototype-name.london.cloudapps.digital/"
    )
    platform_page_context: Dict[str, Union[str, AMPTopMenuForm]] = platform_page(
        mock_request
    )

    assert platform_page_context["page_heading"] == "Dashboard"
    assert platform_page_context["page_title"] == "Dashboard"
    assert platform_page_context["prototype_name"] == "prototype-name"
