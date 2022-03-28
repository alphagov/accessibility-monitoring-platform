from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse


def test_homepage_loads_correctly(admin_client):
    response: HttpResponse = admin_client.get(reverse("homepage:homepage"))
    assert response.status_code == 200
    assertContains(response, "This is the homepage of the report viewer")
