"""
Test context processor of common app
"""

import pytest
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from pytest_django.asserts import assertContains

from ...common.models import FooterLink, FrequentlyUsedLink, Platform
from ...common.sitemap import PlatformPage, Sitemap
from ...common.utils import get_platform_settings
from ...simplified.models import SimplifiedCase
from ..context_processors import platform_page
from ..forms import AMPTopMenuForm

ORGANISATION_NAME: str = "Organisation name two"
USER_FIRST_NAME: str = "Userone"
LINK_LABEL: str = "Custom link"
LINK_URL: str = "https://example.com/custom-link"


class MockRequest:
    def __init__(self, path: str, absolute_uri: str, user: User):
        self.path = path
        self.absolute_uri = absolute_uri
        self.user = user
        self.META = {}
        self.GET = {}
        self.path_info = path

    def build_absolute_uri(self):
        return self.absolute_uri


@pytest.mark.django_db
def test_top_menu_form_present(admin_client):
    """Test search field present"""
    response: HttpResponse = admin_client.get("/")

    assert response.status_code == 200
    assertContains(
        response,
        '<input type="text" name="search" class="govuk-input amp-small-search"'
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
    assertContains(response, USER_FIRST_NAME)


@pytest.mark.django_db
def test_platform_page_template_context():
    """
    Check number of tasks for user, prototype name and
    platform settings added to context.
    """
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    FrequentlyUsedLink.objects.create(label=LINK_LABEL, url=LINK_URL)
    FooterLink.objects.create(label=LINK_LABEL, url=LINK_URL)
    mock_request = MockRequest(
        path="/",
        absolute_uri="https://prototype-name.london.cloudapps.digital/",
        user=user,
    )
    platform_page_context: dict[str, AMPTopMenuForm | str | Platform | int] = (
        platform_page(mock_request)
    )

    assert platform_page_context["platform"] is not None
    assert platform_page_context["number_of_tasks"] == 0

    assert len(platform_page_context["frequently_used_links"]) == 1
    frequently_used_link: FrequentlyUsedLink = platform_page_context[
        "frequently_used_links"
    ][0]
    assert frequently_used_link.label == LINK_LABEL
    assert frequently_used_link.url == LINK_URL

    assert len(platform_page_context["custom_footer_links"]) == 1
    custom_footer_links: list[FooterLink] = platform_page_context[
        "custom_footer_links"
    ][0]
    assert custom_footer_links.label == LINK_LABEL
    assert custom_footer_links.url == LINK_URL

    assert platform_page_context["request_user"] == user


@pytest.mark.django_db
def test_platform_page_case_sitemap_template_context():
    """
    Check sitemap for Case-specific page
    """
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    mock_request = MockRequest(
        path="/simplified/1/view/",
        absolute_uri="https://prototype-name.london.cloudapps.digital/",
        user=user,
    )
    platform_page_context: dict[str, AMPTopMenuForm | str | Platform | int] = (
        platform_page(mock_request)
    )

    assert platform_page_context["sitemap"] is not None

    sitemap: Sitemap = platform_page_context["sitemap"]

    assert sitemap.current_platform_page is not None

    current_platform_page: PlatformPage = sitemap.current_platform_page

    assert current_platform_page.get_name() == "Simplified case overview"
    assert current_platform_page.get_case() is not None
    assert current_platform_page.get_case() == simplified_case


@pytest.mark.django_db
def test_platform_page_non_case_sitemap_template_context():
    """
    Check sitemap for non-Case-specific page
    """
    user: User = User.objects.create(first_name=USER_FIRST_NAME)
    mock_request = MockRequest(
        path="/",
        absolute_uri="https://prototype-name.london.cloudapps.digital/",
        user=user,
    )
    platform_page_context: dict[str, AMPTopMenuForm | str | Platform | int] = (
        platform_page(mock_request)
    )

    assert platform_page_context["sitemap"] is not None

    sitemap: Sitemap = platform_page_context["sitemap"]

    assert sitemap.current_platform_page is not None

    current_platform_page: PlatformPage = sitemap.current_platform_page

    assert current_platform_page.get_name() == "Dashboard"
