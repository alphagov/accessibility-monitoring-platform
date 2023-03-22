"""
Test context processor of common app
"""
import pytest
from pytest_django.asserts import assertContains

from typing import Dict, List, Union

from django.contrib.auth.models import User
from django.http.response import HttpResponse

from ..context_processors import platform_page
from ..forms import AMPTopMenuForm
from ...common.models import FrequentlyUsedLink, Platform
from ...common.utils import get_platform_settings

ORGANISATION_NAME: str = "Organisation name two"
USER_FIRST_NAME: str = "Userone"
LINK_LABEL: str = "Custom link"
LINK_URL: str = "https://example.com/custom-link"


class MockRequest:
    def __init__(self, path: str, absolute_uri: str, user: User):
        self.path = path
        self.absolute_uri = absolute_uri
        self.user = user
        self.META = {}  # pylint: disable=invalid-name

    def build_absolute_uri(self):
        return self.absolute_uri


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
        f"""<div class="govuk-heading-xl amp-margin-bottom-0">{USER_FIRST_NAME}</div>""",
        html=True,
    )


@pytest.mark.django_db
def test_platform_page_template_context():
    """
    Check number of reminders for user, prototype name and
    platform settings added to context.
    """
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    FrequentlyUsedLink.objects.create(label=LINK_LABEL, url=LINK_URL)
    mock_request = MockRequest(
        path="/",
        absolute_uri="https://prototype-name.london.cloudapps.digital/",
        user=user,
    )
    platform_page_context: Dict[
        str, Union[AMPTopMenuForm, str, Platform, int]
    ] = platform_page(mock_request)

    assert platform_page_context["platform"] is not None
    assert platform_page_context["number_of_reminders"] == 0

    assert len(platform_page_context["custom_frequently_used_links"]) == 1
    custom_frequently_used_links: List[FrequentlyUsedLink] = platform_page_context[
        "custom_frequently_used_links"
    ][0]
    assert custom_frequently_used_links.label == LINK_LABEL
    assert custom_frequently_used_links.url == LINK_URL
