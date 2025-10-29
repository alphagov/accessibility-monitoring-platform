"""Tests for utilities for mobile cases"""

from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from ...cases.utils import CaseDetailSection
from ...common.sitemap import Sitemap
from ...common.tests.test_utils import decode_csv_response, validate_csv_response
from ...mobile.csv_export import (
    MOBILE_CASE_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..models import MobileCase, MobileContact
from ..utils import (
    download_mobile_cases,
    download_mobile_equality_body_cases,
    download_mobile_feedback_survey_cases,
    get_mobile_case_detail_sections,
)

ORGANISATION_NAME: str = "Organisation name one"
MOBILE_CONTACT_NAME: str = "Mobile contact name"
MOBILE_CONTACT_TITLE: str = "Mobile contact job title"
MOBILE_CONTACT_DETAILS: str = "Mobile contact details"
MOBILE_CONTACT_INFORMATION: str = "Mobile contact notes"
CSV_EXPORT_FILENAME: str = "mobile_export.csv"


@pytest.mark.django_db
def test_get_mobile_case_detail_sections(rf):
    """Test get_mobile_case_detail_sections builds list of detail sections"""
    mobile_case: MobileCase = MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    request: HttpRequest = rf.get(
        reverse("mobile:case-view-and-search", kwargs={"pk": mobile_case.id}),
    )
    sitemap: Sitemap = Sitemap(request=request)

    sections: list[CaseDetailSection] = get_mobile_case_detail_sections(
        mobile_case=mobile_case, sitemap=sitemap
    )

    assert sections[0].pages[0].display_fields[1].value == ORGANISATION_NAME


@pytest.mark.django_db
def test_download_cases_mobile():
    """Test creation of CSV download of mobile cases"""
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    mobile_case: MobileCase = MobileCase.objects.create()
    mobile_case.created = datetime(2022, 12, 16, tzinfo=timezone.utc)
    mobile_case.save()
    mobile_cases: list[MobileCase] = [mobile_case]
    MobileContact.objects.create(
        mobile_case=mobile_case,
        name=MOBILE_CONTACT_NAME,
        job_title=MOBILE_CONTACT_TITLE,
        contact_details=MOBILE_CONTACT_DETAILS,
        created_by=user,
    )

    response: HttpResponse = download_mobile_cases(
        mobile_cases=mobile_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in MOBILE_CASE_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "1",
        "2",
        "",
        "16/12/2022",
        "Unassigned case",
        "",
        "Mobile",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "EHRC",
        "Unknown",
        "",
        "No",
        "",
        "No",
        "",
        "Mobile contact name",
        "Mobile contact job title",
        "Mobile contact details",
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
        "Not assessed",
        "Not checked",
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
        "",
        "",
        "",
        "iOS: Not assessed\n\nAndroid: Not assessed",
        "",
        "iOS: Not checked\n\nAndroid: Not checked",
        "iOS: n/a\n\nAndroid: n/a",
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
def test_download_feedback_survey_mobile_cases():
    """Test creation of CSV for feedback survey for mobile cases"""
    mobile_case: MobileCase = MobileCase.objects.create(
        recommendation_decision_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
    )
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    MobileContact.objects.create(
        mobile_case=mobile_case,
        contact_details=MOBILE_CONTACT_DETAILS,
        information=MOBILE_CONTACT_INFORMATION,
        created_by=user,
    )
    mobile_cases: list[MobileCase] = [mobile_case]

    response: HttpResponse = download_mobile_feedback_survey_cases(
        cases=mobile_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: list[str] = [
        "1",  # Case no.
        "",  # Organisation name
        "16/12/2022",  # Closing the case date
        "Not selected",  # Enforcement recommendation
        "",  # Enforcement recommendation notes
        "Not assessed",  # statement_compliance_state_12_week
        MOBILE_CONTACT_DETAILS,  # MobileContact email
        MOBILE_CONTACT_INFORMATION,  # MobileContact notes
        "No",  # Feedback survey sent
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_download_equality_body_mobile_cases():
    """Test creation of CSV for equality body for mobile cases"""
    mobile_case: MobileCase = MobileCase.objects.create(
        recommendation_decision_sent_date=datetime(2022, 12, 16, tzinfo=timezone.utc),
    )
    user: User = User.objects.create(
        username="johnsmith", first_name="John", last_name="Smith"
    )
    MobileContact.objects.create(
        mobile_case=mobile_case,
        contact_details=MOBILE_CONTACT_DETAILS,
        information=MOBILE_CONTACT_INFORMATION,
        created_by=user,
    )
    mobile_cases: list[MobileCase] = [mobile_case]

    response: HttpResponse = download_mobile_equality_body_cases(
        mobile_cases=mobile_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in MOBILE_EQUALITY_BODY_COLUMNS_FOR_EXPORT
    ]
    expected_first_data_row: list[str] = [
        "EHRC",
        "Mobile",
        "#M-1",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
        "iOS: n/a\n\nAndroid: n/a",
        "Not selected",
        "",
        "Mobile contact details\nMobile contact notes\n",
        "No",
        "",
        "",
        "",
        "",
        "16/12/2022",
        "",
        "0",
        "0",
        "0",
        "0",
        "iOS: No\n\nAndroid: No",
        "iOS: Not assessed\n\nAndroid: Not assessed",
        "iOS: Not checked\n\nAndroid: Not checked",
        "iOS: n/a\n\nAndroid: n/a",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )
