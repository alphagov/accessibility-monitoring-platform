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
        ("get", reverse("cases:case-export-list")),
        ("post", reverse("cases:case-create")),
        ("get", reverse("cases:case-detail", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-case-metadata", kwargs={"pk": 1})),
        ("post", reverse("cases:manage-contact-details", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-test-results", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-no-psb-response", kwargs={"pk": 1})),
        ("get", reverse("cases:outstanding-issues", kwargs={"pk": 1})),
    ],
)
def test_login_required(method, url, client):
    response: HttpResponse = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"
