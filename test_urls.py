"""
Test top-level urls
"""

import pytest
from django.http.response import HttpResponse
from pytest_django.asserts import assertContains


def test_robots_txt(client):
    """Test robotstxt"""
    response: HttpResponse = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.content == b"User-agent: *\nDisallow: /"


@pytest.mark.parametrize(
    "url",
    ["/security.txt", "/.well-known/security.txt"],
)
def test_security_txt(url, client):
    """Test security txt"""
    response: HttpResponse = client.get(url)

    assert response.status_code == 200
    assertContains(
        response, "Generated at: https://github.com/CO-Cyber-Security/security.txt"
    )
