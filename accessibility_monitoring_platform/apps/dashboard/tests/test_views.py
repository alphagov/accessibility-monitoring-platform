"""
Tests for view - dashboard
"""
from pytest_django.asserts import assertContains

from django.urls import reverse
from django.http import HttpResponse


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
