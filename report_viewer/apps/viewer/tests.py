"""
Test report viewer
"""

import pytest
from typing import Dict, Optional, Tuple
from unittest import mock
from unittest.mock import MagicMock, patch

from pytest_django.asserts import assertContains, assertNotContains
from moto import mock_s3

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader, Template
from django.urls import reverse

from rest_framework.authtoken.models import Token

from common.constants import PLATFORM_VIEWER_DOMAINS

from accessibility_monitoring_platform.apps.cases.models import Case
from accessibility_monitoring_platform.apps.common.models import Platform
from accessibility_monitoring_platform.apps.common.utils import get_platform_settings
from accessibility_monitoring_platform.apps.audits.models import Audit
from accessibility_monitoring_platform.apps.reports.models import (
    Report,
    ReportVisitsMetrics,
)
from accessibility_monitoring_platform.apps.reports.tests.test_utils import MockRequest
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.reports.models import ReportFeedback

from .middleware.report_views_middleware import ReportMetrics
from .utils import get_platform_domain, get_s3_report


def create_report_and_user() -> Tuple[Report, User]:
    """Create report for testing"""
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Token.objects.create(user=user)
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    return report, user


def create_mock_requests_response(s3_report: Optional[S3Report]) -> MagicMock:
    """Create mock requests response based on an S3Report"""
    mock_requests_response: MagicMock = MagicMock()
    mock_requests_response.status_code = 200
    if s3_report is not None:
        mock_requests_response.json.return_value = {
            "guid": s3_report.guid,  # type: ignore
            "html": s3_report.html,  # type: ignore
            "case_id": s3_report.case.id,  # type: ignore
        }
    return mock_requests_response


@pytest.mark.django_db
def test_view_accessibility_statement(client):
    """Test accessibility statement renders"""
    platform: Platform = get_platform_settings()
    platform.report_viewer_accessibility_statement = "# Accessibility statement"
    platform.save()

    response: HttpResponse = client.get(reverse("viewer:accessibility-statement"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Accessibility statement</h1>""",
        html=True,
    )


@pytest.mark.django_db
def test_view_privacy_notice(client):
    """Test privacy notice renders"""
    platform: Platform = get_platform_settings()
    platform.report_viewer_privacy_notice = "# Privacy notice"
    platform.save()

    response: HttpResponse = client.get(reverse("viewer:privacy-notice"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>Privacy notice</h1>""",
        html=True,
    )


@pytest.mark.django_db
@mock_s3
@patch("report_viewer.apps.viewer.utils.requests")
def test_view_report(mock_requests, client):
    """Test view report shows report text from S3"""
    report, user = create_report_and_user()
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html: str = "<p>  This is example text </ p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=report.case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    report_guid_kwargs: Dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    mock_requests.get.return_value = create_mock_requests_response(s3_report=s3_report)

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, "This is example text")


@pytest.mark.django_db
@mock_s3
@patch("report_viewer.apps.viewer.utils.requests")
def test_view_older_report(mock_requests, client):
    """
    Older reports' text is suppressed and a warning shown instead
    """
    report, user = create_report_and_user()
    template: Template = loader.get_template(
        f"""reports_common/accessibility_report_{report.report_version}.html"""
    )
    context: Dict[str, Report] = {"report": report}
    html: str = template.render(context)

    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=report.case,
        user=user,
        report_version=report.report_version,
    )

    html: str = template.render(context)
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=report.case,
        user=user,
        report_version=report.report_version,
    )

    older_s3_report: Optional[S3Report] = S3Report.objects.filter(
        case=report.case
    ).first()
    report_guid_kwargs: Dict[str, int] = {"guid": older_s3_report.guid}  # type: ignore
    mock_requests.get.return_value = create_mock_requests_response(
        s3_report=older_s3_report
    )

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "A newer version of this report is available.")
    assertNotContains(response, '<h2 id="contents">Contents</h2>')

    newest_s3_report: Optional[S3Report] = S3Report.objects.filter(
        case=report.case
    ).last()
    report_guid_kwargs: Dict[str, int] = {"guid": newest_s3_report.guid}  # type: ignore
    mock_requests.get.return_value = create_mock_requests_response(
        s3_report=newest_s3_report
    )

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertNotContains(response, "A newer version of this report is available.")
    assertContains(response, '<h2 id="contents">Contents</h2>')


@pytest.mark.django_db
@mock_s3
@patch("report_viewer.apps.viewer.utils.requests")
def test_view_report_not_on_s3(mock_requests, client):
    """Test view report shows report text from database when not on S3"""
    report, user = create_report_and_user()
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html_on_db: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=report.case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore

    report_guid_kwargs: Dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    mock_requests.get.return_value = create_mock_requests_response(s3_report=s3_report)

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, html_on_db)


def test_report_metric_middleware_client_ip(rf):
    get_response = mock.MagicMock()
    request = rf.get("/")
    rm = ReportMetrics(get_response)
    res = rm.client_ip(request)
    assert res == "127.0.0.1"


def test_report_metric_middleware_string_to_hash(rf):
    secret_key = "12345678"
    get_response = mock.MagicMock()
    request = rf.get("/", HTTP_USER_AGENT="Mozilla/5.0")
    rm = ReportMetrics(get_response)
    res = rm.user_fingerprint(request, secret_key)
    assert res == "Mozilla/5.0127.0.0.112345678"


def test_report_metric_middleware_fingerprint_hash():
    get_response = mock.MagicMock()
    input_str: str = "no_hash_string"
    report_metrics = ReportMetrics(get_response)
    res = report_metrics.four_digit_hash(input_str)
    assert res == 1664


def test_report_metric_middleware_fingerprint_codename():
    get_response = mock.MagicMock()
    input_int: int = 1664
    report_metrics = ReportMetrics(get_response)
    res = report_metrics.fingerprint_codename(input_int)
    assert res == "DogRhinoRhinoChicken"


@pytest.mark.django_db
@mock_s3
@patch("report_viewer.apps.viewer.utils.requests")
def test_report_metric_middleware_successful(mock_requests, client):
    """Test view report shows report text from database when not on S3"""
    report, user = create_report_and_user()
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html_on_db: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=report.case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore

    report_guid_kwargs: Dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    mock_requests.get.return_value = create_mock_requests_response(s3_report=s3_report)

    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    res: int = ReportVisitsMetrics.objects.all().count()
    assert res == 3


@pytest.mark.django_db
@mock_s3
@patch("report_viewer.apps.viewer.utils.requests")
def test_post_report_feedback_form(mock_requests, admin_client):
    """Tests post report feedback saves correctly"""
    example_text: str = "text"
    report, user = create_report_and_user()
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=report.case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: S3Report = S3Report.objects.get(case=report.case)
    mock_requests.get.return_value = create_mock_requests_response(s3_report=s3_report)

    response: HttpResponse = admin_client.post(
        reverse(
            "viewer:viewreport",
            kwargs={"guid": s3_report.guid},
        ),
        {
            "what_were_you_trying_to_do": example_text,
            "what_went_wrong": example_text,
        },
        follow=True,
    )
    report_feedback: ReportFeedback = ReportFeedback.objects.get(guid=s3_report.guid)
    assert response.status_code == 200
    assert report_feedback.guid == s3_report.guid
    assert report_feedback.what_were_you_trying_to_do == example_text
    assert report_feedback.what_went_wrong == example_text
    assert report_feedback.case == report.case
    assertContains(
        response,
        """Thank you for your feedback""",
    )


@pytest.mark.parametrize(
    "platform_domain, http_host",
    PLATFORM_VIEWER_DOMAINS
    + [
        (
            "880-api.london.cloudapps.digital",
            "880-api-report-viewer.london.cloudapps.digital",
        ),
        ("", ""),
    ],
)
def test_platform_domain(platform_domain, http_host):
    """Test that report viewer domain is derived from platform domain"""
    mock_request: MockRequest = MockRequest(http_host=http_host)
    assert get_platform_domain(request=mock_request) == platform_domain  # type: ignore


@patch("report_viewer.apps.viewer.utils.requests")
def test_get_s3_report(mock_requests, admin_client):
    """Test S3Report data from API returned"""
    user: User = User.objects.create()
    Token.objects.create(user=user)
    mock_request: MockRequest = MockRequest(http_host="anything")

    mock_requests_response: MagicMock = create_mock_requests_response(s3_report=None)
    expected_s3_report: Dict[str, str] = {
        "guid": "guid",  # type: ignore
        "html": "html",  # type: ignore
        "case_id": "case.id",  # type: ignore
    }
    mock_requests_response.json.return_value = expected_s3_report
    mock_requests.get.return_value = mock_requests_response

    assert get_s3_report("guid", mock_request) == expected_s3_report  # type: ignore
