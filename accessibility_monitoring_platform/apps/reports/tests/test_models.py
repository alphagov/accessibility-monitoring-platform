"""
Tests for reports models
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

from ...cases.models import Case
from ..models import Report

DOMAIN: str = "example.com"
DATETIME_REPORT_UPDATED: datetime = datetime(2021, 9, 28, tzinfo=timezone.utc)


@pytest.mark.django_db
def test_report_created_timestamp_is_populated():
    """Test the Report created field is populated the first time the Report is saved"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)

    assert report.created is not None
    assert isinstance(report.created, datetime)


@pytest.mark.django_db
def test_report_created_timestamp_is_not_updated():
    """Test the Report created field is not updated on subsequent saves"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)

    original_created_timestamp: datetime = report.created
    report.save()
    updated_report: Report = Report.objects.get(pk=case.id)

    assert updated_report.created == original_created_timestamp


@pytest.mark.django_db
def test_report_wrapper_text_is_correct():
    """
    Test the Report wrapper is correct
    """
    case: Case = Case.objects.create()
    case.domain = DOMAIN
    case.save()
    report: Report = Report.objects.create(case=case)

    assert "title" in report.wrapper
    assert report.wrapper["title"] == f"Accessibility report for {DOMAIN}"


@pytest.mark.django_db
def test_report_template_path_is_correct():
    """
    Test the Report template path is correct
    """
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)

    assert (
        report.template_path
        == "reports_common/accessibility_report_v1_6_0__20250122.html"
    )


@pytest.mark.django_db
def test_latest_s3_report_returned():
    """
    Test the Report.latest_s3_report is the most recent one
    """
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0)
    second_s3_report: S3Report = S3Report.objects.create(
        case=case, version=1, latest_published=True
    )

    assert report.latest_s3_report == second_s3_report


@pytest.mark.django_db
def test_report_updated_updated():
    """Test the report updated field is updated"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)

    with patch("django.utils.timezone.now", Mock(return_value=DATETIME_REPORT_UPDATED)):
        report.save()

    assert report.updated == DATETIME_REPORT_UPDATED
