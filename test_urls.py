"""
Test top-level urls
"""

from unittest.mock import MagicMock, patch

import pytest
from django.http.response import HttpResponse


def test_robots_txt(client):
    """Test robotstxt"""
    response: HttpResponse = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.content == b"User-agent: *\nDisallow: /"


@pytest.mark.parametrize(
    "url",
    ["/security.txt", "/.well-known/security.txt"],
)
@patch("accessibility_monitoring_platform.urls.requests")
def test_security_txt(mock_requests, url, client):
    """Test security txt gotten from vdp.cabinetoffice.gov.u"""
    mock_requests_response: MagicMock = MagicMock()
    mock_requests_response.status_code = 200
    mock_requests.get.return_value = mock_requests_response

    client.get(url)

    mock_requests.get.assert_called_once_with(
        "https://vdp.cabinetoffice.gov.uk/.well-known/security.txt", stream=True
    )
