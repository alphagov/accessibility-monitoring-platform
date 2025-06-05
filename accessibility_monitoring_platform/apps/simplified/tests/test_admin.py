"""
Test - cases admin filter
"""

from django.http import HttpResponse
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains

from ..models import SimplifiedCase

OPEN_CASE_ORGANISATION_NAME: str = "Open case"
CLOSED_CASE_ORGANISATION_NAME: str = "Closed case"


def test_filtering_cases_by_meta_status(admin_client):
    """Test filtering of cases by meta status"""
    SimplifiedCase.objects.create(organisation_name=OPEN_CASE_ORGANISATION_NAME)
    SimplifiedCase.objects.create(
        organisation_name=CLOSED_CASE_ORGANISATION_NAME, is_deactivated=True
    )
    url: str = reverse("admin:cases_case_changelist")

    response: HttpResponse = admin_client.get(f"{url}?meta_status=open")

    assert response.status_code == 200

    assertContains(response, OPEN_CASE_ORGANISATION_NAME)
    assertNotContains(response, CLOSED_CASE_ORGANISATION_NAME)
