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
        ("tech:issue-reports-list", ">Issue reports</h1>"),
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


@pytest.mark.parametrize(
    "fieldname",
    [
        "page_url",
        "page_title",
        "goal_description",
        "issue_description",
        "trello_ticket",
        "notes",
    ],
)
def test_issue_report_list_view_filters(fieldname, admin_client):
    """Test Issue reports list can be filtered by each field"""
    user: User = User.objects.create()
    issue_report: IssueReport = IssueReport.objects.create(created_by=user)
    setattr(issue_report, fieldname, "searchstring")
    issue_report.save()

    response: HttpResponse = admin_client.get(
        f"{reverse('tech:issue-reports-list')}?issue_report_search=SearchString"
    )

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 1 Issue report.</p>', html=True
    )


def test_issue_report_list_view_filter_issue_number(admin_client):
    """Test Issue reports list can be filtered by issue number"""
    user: User = User.objects.create()
    IssueReport.objects.create(created_by=user, issue_number=999)

    response: HttpResponse = admin_client.get(
        f"{reverse('tech:issue-reports-list')}?issue_report_search=999"
    )

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 1 Issue report.</p>', html=True
    )


@pytest.mark.parametrize(
    "fieldname",
    [
        "first_name",
        "last_name",
    ],
)
def test_issue_report_list_view_filter_user_name(fieldname, admin_client):
    """Test Issue reports list can be filtered by user name"""
    user: User = User.objects.create()
    setattr(user, fieldname, "Username1")
    user.save()
    IssueReport.objects.create(created_by=user)

    response: HttpResponse = admin_client.get(
        f"{reverse('tech:issue-reports-list')}?issue_report_search=Username1"
    )

    assert response.status_code == 200

    assertContains(
        response, '<p class="govuk-body-m">Displaying 1 Issue report.</p>', html=True
    )
