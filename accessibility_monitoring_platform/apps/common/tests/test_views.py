"""
Tests for common views
"""
import pytest

from pytest_django.asserts import assertContains

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse

from ..models import Platform
from ..utils import get_platform_settings

EMAIL_SUBJECT = "Email subject"
EMAIL_MESSAGE = "Email message"


def test_contact_admin_page_renders(admin_client):
    """Test contact admin page is rendered"""
    response: HttpResponse = admin_client.get(reverse("common:contact-admin"))

    assert response.status_code == 200
    assertContains(response, "Contact admin")


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


def test_active_qa_audit_page_renders(admin_client):
    """Test active qa audit page is rendered"""
    response: HttpResponse = admin_client.get(reverse("common:edit-active-qa-auditor"))

    assert response.status_code == 200
    assertContains(response, ">Active QA auditor</h1>")


def test_platform_history_renders(admin_client):
    """Test list of changes to platform is rendered"""
    response: HttpResponse = admin_client.get(reverse("common:platform-history"))

    assert response.status_code == 200
    assertContains(response, ">Platform version history</h1>")


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
