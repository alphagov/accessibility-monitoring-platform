"""Tests for utilities for detailed cases"""

from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from ...cases.utils import CaseDetailSection
from ...common.sitemap import Sitemap
from ...common.tests.test_utils import decode_csv_response, validate_csv_response
from ...detailed.csv_export import (
    DETAILED_CASE_COLUMNS_FOR_EXPORT,
    DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..models import Contact, DetailedCase
from ..utils import (
    download_detailed_cases,
    download_detailed_feedback_survey_cases,
    get_detailed_case_detail_sections,
)

ORGANISATION_NAME: str = "Organisation name one"
DETAILED_CONTACT_NAME: str = "Detailed contact name"
DETAILED_CONTACT_TITLE: str = "Detailed contact job title"
DETAILED_CONTACT_DETAILS: str = "Detailed contact details"
DETAILED_CONTACT_INFORMATION: str = "Detailed contact notes"
CSV_EXPORT_FILENAME: str = "detailed_export.csv"


@pytest.mark.django_db
def test_get_detailed_case_detail_sections(rf):
    """Test get_detailed_case_detail_sections builds list of detail sections"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    request: HttpRequest = rf.get(
        reverse("detailed:case-view-and-search", kwargs={"pk": detailed_case.id}),
    )
    sitemap: Sitemap = Sitemap(request=request)

    sections: list[CaseDetailSection] = get_detailed_case_detail_sections(
        detailed_case=detailed_case, sitemap=sitemap
    )

    assert sections[0].pages[0].display_fields[1].value == ORGANISATION_NAME


@pytest.mark.django_db
def test_download_cases_detailed():
    """Test creation of CSV download of detailed cases"""
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    detailed_case: DetailedCase = DetailedCase.objects.create()
    detailed_case.created = datetime(2022, 12, 16, tzinfo=timezone.utc)
    detailed_case.save()
    detailed_cases: list[DetailedCase] = [detailed_case]
    Contact.objects.create(
        detailed_case=detailed_case,
        name=DETAILED_CONTACT_NAME,
        job_title=DETAILED_CONTACT_TITLE,
        contact_details=DETAILED_CONTACT_DETAILS,
        created_by=user,
    )

    response: HttpResponse = download_detailed_cases(
        detailed_cases=detailed_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in DETAILED_CASE_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "1",
        "2",
        "",
        "16/12/2022",
        "Unassigned case",
        "",
        "Detailed",
        "",
        "",
        "",
        "",
        "",
        "",
        "EHRC",
        "Website",
        "Unknown",
        "",
        "No",
        "",
        "No",
        "",
        DETAILED_CONTACT_NAME,
        DETAILED_CONTACT_TITLE,
        DETAILED_CONTACT_DETAILS,
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Not known",
        "Not assessed",
        "Not checked",
        "",
        "No",
        "",
        "",
        "",
        "Not started",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Not known",
        "",
        "Not assessed",
        "",
        "Not checked",
        "",
        "",
        "",
        "Not selected",
        "",
        "",
        "",
        "Case still in progress",
        "No",
        "",
        "",
        "",
        "",
        "",
        "",
        "No (or holding)",
        "",
        "",
        "No",
        "",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_download_feedback_survey_detailed_cases():
    """Test creation of CSV for feedback survey for detailed cases"""
    detailed_case: DetailedCase = DetailedCase.objects.create(
        recommendation_decision_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
    )
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    Contact.objects.create(
        detailed_case=detailed_case,
        contact_details=DETAILED_CONTACT_DETAILS,
        information=DETAILED_CONTACT_INFORMATION,
        created_by=user,
    )
    detailed_cases: list[DetailedCase] = [detailed_case]

    response: HttpResponse = download_detailed_feedback_survey_cases(
        cases=detailed_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: list[str] = [
        "1",  # Case no.
        "",  # Organisation name
        "16/12/2022",  # Closing the case date
        "Not selected",  # Enforcement recommendation
        "",  # Enforcement recommendation notes
        "Not assessed",  # statement_compliance_state_12_week
        DETAILED_CONTACT_DETAILS,  # Contact email
        DETAILED_CONTACT_INFORMATION,  # Contact notes
        "No",  # Feedback survey sent
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )
