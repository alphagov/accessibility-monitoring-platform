"""
Tests for common views
"""
import pytest

from pytest_django.asserts import assertContains

from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse

from ...cases.models import Case

EMAIL_SUBJECT = "Email subject"
EMAIL_MESSAGE = "Email message"


def test_contact_admin_page_renders(admin_client):
    """Test contact admin page is rendered"""
    response: HttpResponse = admin_client.get(reverse("contact-admin"))

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
        reverse("contact-admin"),
        {
            "subject": subject,
            "message": message,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("dashboard:home")

    if subject or message:
        assert len(mailoutbox) == 1
        email = mailoutbox[0]
        assert email.subject == subject
        assert email.body == message
        assert email.from_email == "admin@example.com"
        assert email.to == [settings.CONTACT_ADMIN_EMAIL]
    else:
        assert len(mailoutbox) == 0
