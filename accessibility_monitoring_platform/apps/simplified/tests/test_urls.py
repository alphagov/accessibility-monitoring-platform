"""
Test urls of cases app
"""

import pytest
from django.http.response import HttpResponse
from django.urls import reverse


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", reverse("simplified:case-export-list")),
        ("post", reverse("simplified:case-create")),
        ("get", reverse("simplified:case-detail", kwargs={"pk": 1})),
        ("post", reverse("simplified:edit-case-metadata", kwargs={"pk": 1})),
        ("post", reverse("simplified:manage-contact-details", kwargs={"pk": 1})),
        ("post", reverse("simplified:edit-test-results", kwargs={"pk": 1})),
        ("post", reverse("simplified:edit-no-psb-response", kwargs={"pk": 1})),
        ("get", reverse("simplified:outstanding-issues", kwargs={"pk": 1})),
    ],
)
def test_login_required(method, url, client):
    response: HttpResponse = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"/account/login/?next={url}"
