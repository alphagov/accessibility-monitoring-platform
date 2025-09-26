"""
Test utility functions of cases app
"""

import csv
import io
from typing import Any

import pytest
from django.http import HttpResponse, StreamingHttpResponse

from ...audits.models import Audit
from ...simplified.csv_export import SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT
from ...simplified.models import CaseCompliance, SimplifiedCase
from ..csv_export_utils import download_equality_body_cases

CSV_EXPORT_FILENAME: str = "cases_export.csv"


def decode_csv_response(
    response: StreamingHttpResponse,
) -> tuple[list[str], list[list[str]]]:
    """Decode CSV HTTP response and break into column names and data"""
    content_chunks: list[str] = [
        chunk.decode("utf-8") for chunk in response.streaming_content
    ]
    content: str = "".join(content_chunks)
    csv_reader: Any = csv.reader(io.StringIO(content))
    csv_body: list[list[str]] = list(csv_reader)
    csv_header: list[str] = csv_body.pop(0)
    return csv_header, csv_body


def validate_csv_response(
    csv_header: list[str],
    csv_body: list[list[str]],
    expected_header: list[str],
    expected_first_data_row: list[str],
):
    """Validate csv header and body matches expected data"""
    assert csv_header == expected_header

    first_data_row: list[str] = csv_body[0]

    assert len(first_data_row) == len(expected_first_data_row)

    for position in range(len(first_data_row)):
        assert (
            first_data_row[position] == expected_first_data_row[position]
        ), f"Data mismatch on column {position}: {expected_header[position]}"

    assert first_data_row == expected_first_data_row


@pytest.mark.django_db
def test_download_equality_body_cases():
    """Test creation of CSV for equality bodies"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    CaseCompliance.objects.create(simplified_case=simplified_case)
    simplified_cases: list[SimplifiedCase] = [simplified_case]
    Audit.objects.create(simplified_case=simplified_case)

    response: HttpResponse = download_equality_body_cases(
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
        "1",
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
