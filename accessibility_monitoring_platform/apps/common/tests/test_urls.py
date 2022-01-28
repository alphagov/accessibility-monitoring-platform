"""
Test urls of common app
"""

from django.http.response import HttpResponse
from django.urls import reverse


def test_login_required(client):
    url = reverse("contact-admin")
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"
