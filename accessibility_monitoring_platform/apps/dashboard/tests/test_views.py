"""
Tests for view - dashboard
"""
import pytest
from pytest_django.asserts import assertContains

from django.urls import reverse
from django.http import HttpResponse

from ...users.models import Auditor


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
        ("View+your+cases", "Active QA"),
        ("View+all+cases", "Unassigned QA cases"),
    ],
)
def test_dashboard_shows_qa_auditors(
    dashboard_view, expected_qa_column, admin_client, admin_user
):
    """Tests if dashboard views are showing the expected QA auditors column"""
    Auditor.objects.create(user=admin_user, active_qa_auditor=admin_user)
    response: HttpResponse = admin_client.get(
        f'{reverse("dashboard:home")}?view={dashboard_view}'
    )

    assert response.status_code == 200
    assertContains(response, expected_qa_column)
