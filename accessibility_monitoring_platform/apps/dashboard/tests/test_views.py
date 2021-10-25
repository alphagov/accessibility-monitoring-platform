"""
Tests for view - dashboard
"""
import pytest
from pytest_django.asserts import assertContains

from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.urls import reverse


def test_dashboard_loads_correctly_when_user_logged_in(admin_client):
    """Tests if a logged in user can access the Dashboard"""
    response: HttpResponse = admin_client.get(reverse("dashboard:home"))

    assert response.status_code == 200
    assertContains(response, "Dashboard")


def test_dashboard_redirects_to_login_when_user_not_logged_in(client):
    """Tests if a unauthenticated user returns a 302 response"""
    url: str = reverse("dashboard:home")
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"


@pytest.mark.parametrize(
    "dashboard_view, expected_qa_column",
    [
        ("View+your+cases", "On call"),
        ("View+all+cases", "Unassigned QA cases"),
    ],
)
def test_dashboard_shows_qa_auditors(dashboard_view, expected_qa_column, admin_client):
    """Tests if dashboard views are showing the expected QA auditors column"""
    response: HttpResponse = admin_client.get(
        f'{reverse("dashboard:home")}?view={dashboard_view}'
    )

    assert response.status_code == 200
    assertContains(response, expected_qa_column)


@pytest.mark.parametrize(
    "qa_auditor, expected_view",
    [
        (True, "All cases"),
        (False, "Your cases"),
    ],
)
def test_dashboard_shows_all_cases_by_default_to_qa_auditors(
    qa_auditor, expected_view, admin_client, admin_user
):
    """Tests dashboard shows all cases by default to members of the QA auditor group"""
    if qa_auditor:
        qa_auditor_group: Group = Group.objects.create(name="QA auditor")
        qa_auditor_group.user_set.add(admin_user)  # type: ignore

    response: HttpResponse = admin_client.get(f'{reverse("dashboard:home")}')

    assert response.status_code == 200
    assertContains(response, f'<h1 class="govuk-heading-xl">{expected_view}</h1>')
