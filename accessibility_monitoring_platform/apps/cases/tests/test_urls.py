"""
Test urls of cases app
"""

import pytest
from django.http.response import HttpResponse
from django.urls import reverse


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", reverse("cases:case-list")),
    ],
)
def test_login_required(method, url, client):
    response: HttpResponse = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"
