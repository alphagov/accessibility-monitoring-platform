"""
Test urls of cases app
"""

from django.http.response import HttpResponse
import pytest

from django.urls import reverse


@pytest.mark.parametrize("method,url", [
    ("get", reverse("cases:case-list")),
    ("get", reverse("cases:case-export-list")),
    ("get", reverse("cases:case-export-single", kwargs={"pk": 1})),
    ("post", reverse("cases:case-create")),
    ("get", reverse("cases:case-detail", kwargs={"pk": 1})),
    ("post", reverse("cases:edit-website-details", kwargs={"pk": 1})),
    ("post", reverse("cases:edit-contact-details", kwargs={"pk": 1})),
    ("post", reverse("cases:edit-test-results", kwargs={"pk": 1})),
    ("post", reverse("cases:edit-report-details", kwargs={"pk": 1})),
    ("post", reverse("cases:edit-post-report-details", kwargs={"pk": 1})),
    ("get", reverse("cases:archive-case", kwargs={"pk": 1})),
])
def test_login_required(method, url, client):
    response: HttpResponse = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"
