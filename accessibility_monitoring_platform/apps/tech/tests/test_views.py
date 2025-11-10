"""Tests for tech team app views"""

import logging

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Audit
from ...common.models import IssueReport
from ...reports.models import Report
from ...simplified.models import SimplifiedCase
from ...users.tests.test_views import VALID_PASSWORD, VALID_USER_EMAIL, create_user

LOG_MESSAGE: str = "Hello"


@pytest.mark.parametrize(
    "url_name,expected_header",
    [
        ("tech:platform-checking", ">Tools and sitemap</h1>"),
    ],
)
def test_page_renders(url_name, expected_header, admin_client):
    """Test common page is rendered"""
    response: HttpResponse = admin_client.get(reverse(url_name))

    assert response.status_code == 200
    assertContains(response, expected_header)


def test_platform_checking_writes_log(admin_client, caplog):
    """Test platform checking writes to log"""
    response: HttpResponse = admin_client.post(
        reverse("tech:platform-checking"),
        {
            "level": logging.WARNING,
            "message": LOG_MESSAGE,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("tech:platform-checking")
    assert caplog.record_tuples == [
        ("accessibility_monitoring_platform.apps.tech.views", 30, LOG_MESSAGE)
    ]


@pytest.mark.django_db
def test_platform_checking_staff_access(client):
    """Tests if staff users can access platform checking"""
    user: User = create_user()
    user.is_staff = True
    user.save()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse("tech:platform-checking"))

    assert response.status_code == 200
    assertContains(response, "Tools and sitemap")


@pytest.mark.django_db
def test_platform_checking_non_staff_access(client):
    """Tests non-staff users cannot access platform checking"""
    create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse("tech:platform-checking"))

    assert response.status_code == 403


def test_reference_implementations_page(admin_client):
    """Test that the reference implementation page renders"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(reverse("tech:reference-implementation"))

    assert response.status_code == 200

    assertContains(response, "Reference implementation")
