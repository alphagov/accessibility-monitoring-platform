import pytest
from django.http import HttpResponse

from ...audits.models import Audit
from ...common.tests.test_utils import decode_csv_response, validate_csv_response
from ...simplified.csv_export import SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT
from ...simplified.models import CaseCompliance, SimplifiedCase
from ..utils import download_equality_body_simplified_cases, get_exportable_cases
from .test_forms import CUTOFF_DATE, create_exportable_case

CSV_EXPORT_FILENAME: str = "cases_export.csv"


@pytest.mark.django_db
def test_download_equality_body_simplified_cases():
    """Test creation of CSV for equality bodies simplified cases"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = download_equality_body_simplified_cases(
        cases=simplified_cases, filename=CSV_EXPORT_FILENAME
    )

    assert response.status_code == 200

    assert response.headers == {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename={CSV_EXPORT_FILENAME}",
    }

    csv_header, csv_body = decode_csv_response(response)

    expected_header: list[str] = [
        column.column_header for column in SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT
    ]

    expected_first_data_row: list[str] = [
        "EHRC",
        "Simplified",
        "#S-1",
        "",
        "",
        "",
        "",
        "",
        "",
        "No",
        "",
        "Not selected",
        "",
        "",
        "No",
        "",
        "",
        "",
        "",
        "",
        "",
        "0",
        "0",
        "0",
        "n/a",
        "Yes",
        "Not assessed",
        "Not checked",
        "",
    ]

    validate_csv_response(
        csv_header=csv_header,
        csv_body=csv_body,
        expected_header=expected_header,
        expected_first_data_row=expected_first_data_row,
    )


@pytest.mark.django_db
def test_get_exportable_case():
    """Tests get_exportable_cases gets exportable cases for enforcement body"""
    simplified_case: SimplifiedCase = create_exportable_case()

    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.EHRC,
        ).first()
        == simplified_case
    )
    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.ECNI,
        ).first()
        is None
    )

    simplified_case.enforcement_body = SimplifiedCase.EnforcementBody.ECNI
    simplified_case.save()

    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.EHRC,
        ).first()
        is None
    )
    assert (
        get_exportable_cases(
            cutoff_date=CUTOFF_DATE,
            enforcement_body=SimplifiedCase.EnforcementBody.ECNI,
        ).first()
        == simplified_case
    )
