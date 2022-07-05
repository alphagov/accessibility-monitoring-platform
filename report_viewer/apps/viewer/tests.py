"""
Test report viewer
"""
import pytest

from typing import Dict, Optional

from pytest_django.asserts import assertContains, assertNotContains
from moto import mock_s3

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader, Template
from django.urls import reverse

from accessibility_monitoring_platform.apps.cases.models import Case
from accessibility_monitoring_platform.apps.audits.models import Audit
from accessibility_monitoring_platform.apps.reports.models import Report
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report


def test_view_accessibility_statement(client):
    """Test accessibility statement renders"""
    response: HttpResponse = client.get(reverse("viewer:accessibility-statement"))

    assert response.status_code == 200
    assertContains(
        response,
        """<h1 class="govuk-heading-xl">Accessibility statement</h1>""",
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
        f"""reports/accessibility_report_{report.report_version}.html"""
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
    HTML_ON_DB: str = "<p>Text on DB</p>"
    s3_read_write_report.upload_string_to_s3_as_html(
        html_content="<p>Text on S3</p>",
        case=case,
        user=user,
        report_version="v1_202201401",
    )
    s3_report: Optional[S3Report] = S3Report.objects.all().first()
    s3_report.s3_directory = "not-a-valid-dir"  # type: ignore
    s3_report.html = HTML_ON_DB  # type: ignore
    s3_report.save()  # type: ignore

    report_guid_kwargs: Dict[str, int] = {"guid": s3_report.guid}  # type: ignore
    response: HttpResponse = client.get(
        reverse("viewer:viewreport", kwargs=report_guid_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, HTML_ON_DB)
