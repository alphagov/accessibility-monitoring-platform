"""
Tests for reports views
"""
import pytest
from typing import Dict

from pytest_django.asserts import assertContains

from django.http import HttpResponse
from django.urls import reverse

from ...audits.models import Audit
from ...cases.models import Case

from ..models import Report, PublishedReport


def create_report() -> Report:
    """Create a report for testing"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    report: Report = Report.objects.create(case=case)
    PublishedReport.objects.create(report=report)
    return report


def test_create_report_redirects(admin_client):
    """Test that report create redirects to report metadata"""
    case: Case = Case.objects.create()
    path_kwargs: Dict[str, int] = {"case_id": case.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-create", kwargs=path_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:edit-report-metadata", kwargs={"pk": 1})


def test_rebuild_report_redirects(admin_client):
    """Test that report rebuild redirects to report details"""
    report: Report = create_report()
    pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(
        reverse("reports:report-rebuild", kwargs=pk_kwargs),
    )

    assert response.status_code == 302

    assert response.url == reverse("reports:report-detail", kwargs=pk_kwargs)


@pytest.mark.parametrize(
    "path_name, expected_header",
    [
        ("reports:report-detail", ">View report</h1>"),
        ("reports:edit-report-metadata", ">Report metadata</h1>"),
        ("reports:published-report-list", ">Report versions</h1>"),
    ],
)
def test_case_specific_page_loads(path_name, expected_header, admin_client):
    """Test that the report-specific view page loads"""
    report: Report = create_report()
    pk_kwargs: Dict[str, int] = {"pk": report.id}  # type: ignore

    response: HttpResponse = admin_client.get(reverse(path_name, kwargs=pk_kwargs))

    assert response.status_code == 200

    assertContains(response, expected_header)
