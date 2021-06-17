"""
Test urls of websites app
"""

import pytest

from django.http.response import HttpResponse
from django.urls import reverse

URLS = [
    reverse("websites:website-list"),
    reverse("websites:website-export-list"),
]


@pytest.mark.parametrize("url", URLS)
def test_login_required(url, client):
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"
