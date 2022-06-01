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
        ("get", reverse("cases:case-export-single", kwargs={"pk": 1})),
        ("post", reverse("cases:case-create")),
        ("get", reverse("cases:case-detail", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-case-details", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-contact-details", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-test-results", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-report-details", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-report-correspondence", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-no-psb-response", kwargs={"pk": 1})),
        ("post", reverse("cases:edit-report-followup-due-dates", kwargs={"pk": 1})),
    ],
)
def test_login_required(method, url, client):
    response: HttpResponse = getattr(client, method)(url)

    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"
