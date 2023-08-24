"""
Check test and test platforms are working. Non-destructive checks only!
"""
import requests


def check_url(url: str):
    response: requests.models.Response = requests.get(url)
    assert (
        response.status_code == 200
    ), f"Unexpected response status: {response.status_code} (on {url})"
    assert (
        "Strict-Transport-Security" in response.headers
    ), f"Strict-Transport-Security header missing (on {url})"
    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=2592000; includeSubDomains; preload"
    ), f"Unexpected Strict-Transport-Security: {response.headers['Strict-Transport-Security']} (on {url})"


def main():
    for url in [
        "https://platform-test.accessibility-monitoring.service.gov.uk/",
        "https://platform-test.accessibility-monitoring.service.gov.uk/platform-admin/",
        "https://platform.accessibility-monitoring.service.gov.uk/",
        "https://platform.accessibility-monitoring.service.gov.uk/platform-admin/",
    ]:
        check_url(url)


if __name__ == "__main__":
    main()
