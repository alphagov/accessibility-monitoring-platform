"""
Test report viewer
"""

import logging
from datetime import date
from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import Template, loader
from django.urls import reverse
from moto import mock_aws
from pytest_django.asserts import assertContains, assertNotContains

from accessibility_monitoring_platform.apps.audits.models import Audit
from accessibility_monitoring_platform.apps.cases.models import Case
from accessibility_monitoring_platform.apps.common.models import (
    Platform,
    UserCacheUniqueHash,
)
from accessibility_monitoring_platform.apps.common.utils import get_platform_settings
from accessibility_monitoring_platform.apps.reports.models import (
    Report,
    ReportVisitsMetrics,
)
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport

from .middleware.report_views_middleware import ReportMetrics
from .utils import show_warning


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
def test_more_information(client):
    """Test more information about monitoring renders"""
    platform: Platform = get_platform_settings()
    platform.more_information_about_monitoring = "# More information"
    platform.save()

    response: HttpResponse = client.get(reverse("viewer:more-information"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1>More information</h1>""",
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
@mock_aws
def test_view_report(client):
    """Test view report shows report text from S3"""
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Report.objects.create(case=case)
    Audit.objects.create(case=case)
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html: str = "<p>  This is example text </ p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3report: S3Report | None = S3Report.objects.all().first()

    report_guid_kwargs: dict[str, int] = {"guid": s3report.guid}  # type: ignore
    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, "This is example text")


@pytest.mark.django_db
@mock_aws
def test_view_older_report(client):
    """
    Older reports' text is suppressed and a warning shown instead
    """
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)

    template: Template = loader.get_template(
        f"""reports_common/accessibility_report_{report.report_version}.html"""
    )
    context: dict[str, Report] = {"report": report}
    html: str = template.render(context)

    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=case,
        user=user,
        report_version=report.report_version,
    )

    html: str = template.render(context)
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content=html,
        case=case,
        user=user,
        report_version=report.report_version,
    )

    older_s3report: S3Report | None = S3Report.objects.filter(case=case).first()
    report_guid_kwargs: dict[str, int] = {"guid": older_s3report.guid}  # type: ignore

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "A newer version of this report is available.")
    assertNotContains(response, '<h2 id="contents">Contents</h2>')

    newest_s3report: S3Report | None = S3Report.objects.filter(case=case).last()
    report_guid_kwargs: dict[str, int] = {"guid": newest_s3report.guid}  # type: ignore

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertNotContains(response, "A newer version of this report is available.")
    assertContains(response, '<h2 id="contents">Contents</h2>')


@pytest.mark.django_db
@mock_aws
def test_view_report_not_on_s3(client):
    """Test view report shows report text from database when not on S3"""
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Report.objects.create(case=case)
    Audit.objects.create(case=case)
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html_on_db: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: S3Report | None = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore
    guid: str = s3_report.guid  # type: ignore

    report_guid_kwargs: dict[str, str] = {"guid": guid}

    logger = logging.getLogger("report_viewer.apps.viewer.views")
    with mock.patch.object(logger, "warning") as mock_warning:
        response: HttpResponse = client.get(
            reverse("viewer:viewreport", kwargs=report_guid_kwargs)
        )
        assert response.status_code == 200

        assertContains(response, html_on_db)
        mock_warning.assert_called_once_with("Report %s not found on S3", guid)


def test_report_metric_middleware_client_ip(rf):
    get_response = mock.MagicMock()
    request = rf.get("/")
    rm = ReportMetrics(get_response)
    res = rm.client_ip(request)
    assert res == "127.0.0.1"


def test_report_metric_middleware_string_to_hash(rf):
    get_response = mock.MagicMock()
    request = rf.get("/", HTTP_USER_AGENT="Mozilla/5.0")
    rm = ReportMetrics(get_response)
    res = rm.user_fingerprint(request)
    assert res == "Mozilla/5.0127.0.0.1"


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


def test_extract_guid_from_url_returns_guid():
    get_response = mock.MagicMock()
    guid: str = "5ef13c2e-cead-47b0-853a-3fbad79d6385"
    input_address: str = f"https://website.com/{guid}"
    report_metrics = ReportMetrics(get_response)
    res: str | None = report_metrics.extract_guid_from_url(input_address)
    assert res == guid


def test_extract_guid_from_url_returns_none():
    get_response = mock.MagicMock()
    report_metrics = ReportMetrics(get_response)

    res: str | None = report_metrics.extract_guid_from_url("https://website.com/")
    assert res is None

    res: str | None = report_metrics.extract_guid_from_url(
        "https://website.com/5ef13c2e-cead-47b0-853a-3fbad79d638"
    )
    assert res is None


@pytest.mark.django_db
@mock_aws
def test_report_metric_middleware_successful(client):
    """Test logs report views to database"""
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Report.objects.create(case=case)
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html_on_db: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: S3Report | None = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore

    report_guid_kwargs: dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    res: int = ReportVisitsMetrics.objects.all().count()
    assert res == 3


@pytest.mark.django_db
@mock_aws
def test_report_metric_middleware_ignore_user(client, rf):
    """Test report view logs ignores user"""
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Report.objects.create(case=case)
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    html_on_db: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: S3Report | None = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore

    get_response = mock.MagicMock()
    report_metrics = ReportMetrics(get_response)

    request = rf.get("/")
    string_to_hash: str = report_metrics.user_fingerprint(request)
    fingerprint_hash: int = report_metrics.four_digit_hash(string_to_hash)
    UserCacheUniqueHash.objects.create(
        user=user,
        fingerprint_hash=fingerprint_hash,
    )
    assert UserCacheUniqueHash.objects.all().count() == 1

    report_guid_kwargs: dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    res: int = ReportVisitsMetrics.objects.all().count()
    assert res == 0


@pytest.mark.parametrize(
    "today, expected_result",
    [
        (date(2023, 7, 2), False),
        (date(2023, 7, 3), True),
        (date(2023, 7, 21), True),
        (date(2023, 7, 22), False),
    ],
)
def test_show_warning(today, expected_result):
    with mock.patch("report_viewer.apps.viewer.utils.date") as mock_date:
        mock_date.today.return_value = today
        assert show_warning() is expected_result
