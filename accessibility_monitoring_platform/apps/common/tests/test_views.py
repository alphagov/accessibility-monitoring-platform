"""
Tests for common views
"""
import pytest

from pytest_django.asserts import assertContains, assertNotContains

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse

from ..models import Platform
from ..utils import get_platform_settings

EMAIL_SUBJECT: str = "Email subject"
EMAIL_MESSAGE: str = "Email message"
ISSUE_REPORT_LINK: str = """<a href="/common/report-issue/?page_url=/"
target="_blank"
class="govuk-link govuk-link--no-visited-state">report</a>"""


@pytest.mark.parametrize(
    "url_name,expected_header",
    [
        ("common:contact-admin", "Contact admin"),
        ("common:edit-active-qa-auditor", ">Active QA auditor</h1>"),
        ("common:platform-history", ">Platform version history</h1>"),
        ("common:issue-report", ">Report an issue</h1>"),
        ("common:accessibility-statement", ">Accessibility statement</h1>"),
        ("common:privacy-notice", ">Privacy notice</h1>"),
        ("common:markdown-cheatsheet", ">Markdown cheatsheet</h1>"),
        ("common:metrics-case", ">Case metrics</h1>"),
    ],
)
def test_page_renders(url_name, expected_header, admin_client):
    """Test common page is rendered"""
    response: HttpResponse = admin_client.get(reverse(url_name))

    assert response.status_code == 200
    assertContains(response, expected_header)


@pytest.mark.parametrize(
    "subject,message",
    [
        (EMAIL_SUBJECT, EMAIL_MESSAGE),
        ("", ""),
        (EMAIL_SUBJECT, ""),
        ("", EMAIL_MESSAGE),
    ],
)
def test_contact_admin_page_sends_email(subject, message, admin_client, mailoutbox):
    """Test contact admin messages are emailed if message or subject entered"""
    response: HttpResponse = admin_client.post(
        reverse("common:contact-admin"),
        {
            "subject": subject,
            "message": message,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard:home")  # type: ignore

    if subject or message:
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.subject == subject
        assert email.body == message
        assert email.from_email == "admin@example.com"
        assert email.to == [settings.CONTACT_ADMIN_EMAIL]
    else:
        assert len(mailoutbox) == 0


@pytest.mark.django_db
def test_view_accessibility_statement(client):
    """Test accessibility statement renders. No login required"""
    platform: Platform = get_platform_settings()
    platform.platform_accessibility_statement = "# Accessibility statement header"
    platform.save()

    response: HttpResponse = client.get(reverse("common:accessibility-statement"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Accessibility statement header</h1>""",
        html=True,
    )


@pytest.mark.django_db
def test_view_privacy_notice(client):
    """Test privacy notice renders. No login required."""
    platform: Platform = get_platform_settings()
    platform.platform_privacy_notice = "# Privacy notice header"
    platform.save()

    response: HttpResponse = client.get(reverse("common:privacy-notice"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Privacy notice header</h1>""",
        html=True,
    )


@pytest.mark.parametrize(
    "prototype_name,issue_report_link_expected",
    [
        ("", True),
        ("TEST", True),
        ("anything-else", False),
    ],
)
def test_issue_report_link(prototype_name, issue_report_link_expected, admin_client):
    """
    Test issue report link is rendered on live and test platforms
    but not on prototypes.
    """
    settings.AMP_PROTOTYPE_NAME = prototype_name
    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    if issue_report_link_expected:
        assertContains(response, ISSUE_REPORT_LINK, html=True)
    else:
        assertNotContains(response, ISSUE_REPORT_LINK, html=True)
