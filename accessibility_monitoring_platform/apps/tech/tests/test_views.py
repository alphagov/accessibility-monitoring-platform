"""Tests for tech team app views"""

import logging

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains

from ...audits.models import Audit
from ...reports.models import Report
from ...simplified.models import SimplifiedCase
from ...users.tests.test_views import VALID_PASSWORD, VALID_USER_EMAIL, create_user

LOG_MESSAGE: str = "Hello"


@pytest.mark.parametrize(
    "url_name, page_name",
    [
        ("tech:reference-implementation", ">Reference implementation</h1>"),
        ("tech:platform-checking", ">Check logging and exceptions</h1>"),
        ("tech:equality-body-csv-metadata", ">Equality body CSV metadata</h1>"),
        ("tech:sitemap", ">Sitemap</h1>"),
    ],
)
def test_page_renders(url_name, page_name, admin_client):
    """Test common page is rendered"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    Report.objects.create(base_case=simplified_case)

    response: HttpResponse = admin_client.get(reverse(url_name))

    assert response.status_code == 200
    assertContains(response, page_name)


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


@pytest.mark.parametrize(
    "url_name, page_name",
    [
        ("tech:reference-implementation", "Reference implementation"),
        ("tech:platform-checking", "Check logging and exceptions"),
        ("tech:equality-body-csv-metadata", "Equality body CSV metadata"),
        ("tech:sitemap", "Sitemap"),
    ],
)
@pytest.mark.django_db
def test_tech_page_staff_access(url_name, page_name, client):
    """Tests if staff users can access tech pages"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    Audit.objects.create(simplified_case=simplified_case)
    Report.objects.create(base_case=simplified_case)

    user: User = create_user()
    user.is_staff = True
    user.save()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse(url_name))

    assert response.status_code == 200
    assertContains(response, page_name)


@pytest.mark.parametrize(
    "url_name",
    [
        "tech:reference-implementation",
        "tech:platform-checking",
        "tech:equality-body-csv-metadata",
        "tech:sitemap",
    ],
)
@pytest.mark.django_db
def test_platform_checking_non_staff_access(url_name, client):
    """Tests non-staff users cannot access tech pages"""
    create_user()
    client.login(username=VALID_USER_EMAIL, password=VALID_PASSWORD)

    response: HttpResponse = client.get(reverse(url_name))

    assert response.status_code == 403
