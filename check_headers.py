import requests


def check_response(response):
    assert (
        response.status_code == 200
    ), f"Unexpected response status: {response.status_code}"
    assert (
        "Strict-Transport-Security" in response.headers
    ), "Strict-Transport-Security header missing"
    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=2592000; includeSubDomains; preload"
    ), f"Unexpected Strict-Transport-Security: {response.headers['Strict-Transport-Security']}"


def main():
    for url in [
        "https://platform-test.accessibility-monitoring.service.gov.uk/",
        "https://platform-test.accessibility-monitoring.service.gov.uk/admin/",
        "https://platform.accessibility-monitoring.service.gov.uk/",
        "https://platform.accessibility-monitoring.service.gov.uk/admin/",
    ]:
        response = requests.get(url)
        check_response(response)
