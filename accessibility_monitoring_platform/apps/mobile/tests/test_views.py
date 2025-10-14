"""
Tests for cases views
"""

import pytest
from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains


@pytest.mark.parametrize(
    "path_name, expected_content",
    [
        (
            "mobile:case-create",
            '<h1 class="govuk-heading-xl">Create mobile case</h1>',
        ),
    ],
)
def test_non_case_specific_page_loads(path_name, expected_content, admin_client):
    """Test that the non-case-specific view page loads"""
    response: HttpResponse = admin_client.get(reverse(path_name))

    assert response.status_code == 200
    assertContains(response, expected_content, html=True)
