"""
Test urls of cases app
"""

import pytest
from pytest_django.asserts import assertContains

from django.http.response import HttpResponse
from django.urls import reverse


@pytest.mark.parametrize(
    "url, page_title",
    [
        (reverse("cases:case-list"), "Search"),
        (reverse("cases:case-create"), "Create case"),
        (reverse("contact-admin"), "Contact admin"),
        (reverse("issue-report"), "Report an issue"),
    ],
)
def test_page_title_present(url, page_title, admin_client):
    response: HttpResponse = admin_client.get(url)

    assert response.status_code == 200
    assertContains(response, f'<h1 class="govuk-heading-xl">{page_title}</h1>')
