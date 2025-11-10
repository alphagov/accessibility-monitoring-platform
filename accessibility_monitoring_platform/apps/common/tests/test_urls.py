"""
Test urls of common app
"""

import pytest
from django.http.response import HttpResponse
from django.urls import reverse


@pytest.mark.parametrize(
    "url_name",
    [
        "common:contact-admin",
        "common:edit-active-qa-auditor",
        "common:platform-history",
        "common:markdown-cheatsheet",
    ],
)
def test_login_required(url_name, client):
    url = reverse(url_name)
    response: HttpResponse = client.get(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"
