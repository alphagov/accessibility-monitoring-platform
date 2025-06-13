"""Test root redirect and healthcheck endpoints"""


def test_root_redirect(client):
    """Test that the root redirect works"""
    response = client.get("/")

    assert response.status_code == 302
    assert response.url == "https://www.gov.uk/guidance/public-sector-website-and-mobile-application-accessibility-monitoring/"


def test_healthcheck_url_works(client):
    """Test that the healthcheck endpoint responds correctly"""
    response = client.get("/healthcheck/")

    assert response.status_code == 200
    assert response.json() == {"healthcheck": "ok"}
