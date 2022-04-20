import pytest
from pytest_django.asserts import assertContains
from typing import Dict
from moto import mock_s3
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from accessibility_monitoring_platform.apps.cases.models import Case
from accessibility_monitoring_platform.apps.audits.models import Audit
from accessibility_monitoring_platform.apps.reports.models import Report
from accessibility_monitoring_platform.apps.s3_read_write.utils import S3ReadWriteReport
from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report


@pytest.mark.django_db
@mock_s3
def test_view_report(admin_client):
    case: Case = Case.objects.create()
    user: User = User.objects.create()
    Report.objects.create(case=case)
    Audit.objects.create(case=case)
    S3RWReport: S3ReadWriteReport = S3ReadWriteReport()
    html = "<p>  This is example text </ p>"
    S3RWReport.upload_string_to_s3_as_html(
        html_content=html,
        case=case,
        user=user,  # type: ignore
        report_version="v1_202201401"
    )
    s3report: S3Report = S3Report.objects.all()[0]

    report_pk_kwargs: Dict[str, int] = {"guid": s3report.guid}  # type: ignore
    response: HttpResponse = admin_client.get(
        reverse("viewer:viewreport", kwargs=report_pk_kwargs)
    )
    assert response.status_code == 200

    assertContains(response, "This is example text")
