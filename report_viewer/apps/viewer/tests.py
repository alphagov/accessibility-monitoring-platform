"""
Test report viewer
"""
import pytest

from typing import Dict, Optional
from unittest import mock
import logging

from pytest_django.asserts import assertContains, assertNotContains
from moto import mock_s3

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader, Template
from django.urls import reverse

from accessibility_monitoring_platform.apps.cases.models import Case
from accessibility_monitoring_platform.apps.common.models import Platform
from accessibility_monitoring_platform.apps.common.utils import get_platform_settings
from accessibility_monitoring_platform.apps.audits.models import Audit
from accessibility_monitoring_platform.apps.reports.models import (
    Report,
    ReportVisitsMetrics,
)
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report
from accessibility_monitoring_platform.apps.reports.models import ReportFeedback

from .middleware.report_views_middleware import ReportMetrics


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
@mock_s3
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
    s3report: Optional[S3Report] = S3Report.objects.all().first()

    report_guid_kwargs: Dict[str, int] = {"guid": s3report.guid}  # type: ignore
    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, "This is example text")


@pytest.mark.django_db
@mock_s3
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
    context: Dict[str, Report] = {"report": report}
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

    older_s3report: Optional[S3Report] = S3Report.objects.filter(case=case).first()
    report_guid_kwargs: Dict[str, int] = {"guid": older_s3report.guid}  # type: ignore

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertContains(response, "A newer version of this report is available.")
    assertNotContains(response, '<h2 id="contents">Contents</h2>')

    newest_s3report: Optional[S3Report] = S3Report.objects.filter(case=case).last()
    report_guid_kwargs: Dict[str, int] = {"guid": newest_s3report.guid}  # type: ignore

    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )

    assert response.status_code == 200

    assertNotContains(response, "A newer version of this report is available.")
    assertContains(response, '<h2 id="contents">Contents</h2>')


@pytest.mark.django_db
@mock_s3
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
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore
    guid: str = s3_report.guid  # type: ignore

    report_guid_kwargs: Dict[str, str] = {"guid": guid}

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
def test_report_metric_middleware_successful(client):
    """Test view report shows report text from database when not on S3"""
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
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = html_on_db  # type: ignore
    s3_report.save()  # type: ignore

    report_guid_kwargs: Dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    client.get(reverse("viewer:viewreport", kwargs=report_guid_kwargs))
    res: int = ReportVisitsMetrics.objects.all().count()
    assert res == 3


@pytest.mark.django_db
@mock_s3
def test_post_report_feedback_form(admin_client):
    """Tests post report feedback saves correctly"""
    example_text: str = "text"
    user: User = User.objects.create()
    case: Case = Case.objects.create(organisation_name="org_name")
    Report.objects.create(case=case)
    s3_read_write_report: S3ReadWriteReport = S3ReadWriteReport()
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: S3Report = S3Report.objects.get(case=case)
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
    assert report_feedback.case == case
    assertContains(
        response,
        """Thank you for your feedback""",
    )
