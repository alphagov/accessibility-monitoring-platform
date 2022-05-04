"""
Tests for reports models
"""
import pytest
from datetime import datetime

from accessibility_monitoring_platform.apps.s3_read_write.models import S3Report

from ...cases.models import Case

from ..models import Report, Section, TableRow

DOMAIN: str = "example.com"


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
    updated_report: Report = Report.objects.get(pk=case.id)  # type: ignore

    assert updated_report.created == original_created_timestamp


@pytest.mark.django_db
def test_section_has_anchor():
    """Test the Section has an anchor property"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)

    assert section.anchor == f"report-section-{section.id}"  # type: ignore


@pytest.mark.django_db
def test_deleted_table_rows_are_not_visible():
    """Test the Section visible_table_rows property doesn't include deleted rows"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    TableRow.objects.create(section=section, row_number=1, is_deleted=True)
    undeleted_table_row: TableRow = TableRow.objects.create(
        section=section, row_number=2
    )

    assert section.visible_table_rows.count() == 1
    assert undeleted_table_row in section.visible_table_rows


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

    assert report.template_path == "reports/accessibility_report_v1_0_0__20220406.html"


@pytest.mark.django_db
def test_latest_s3_report_returned():
    """
    Test the Report.latest_s3_report is the most recent one
    """
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    S3Report.objects.create(case=case, version=0)
    second_s3_report: S3Report = S3Report.objects.create(case=case, version=1)

    assert report.latest_s3_report == second_s3_report
