"""Utility functions for CSV exports"""

from django.db.models import QuerySet
from django.http import StreamingHttpResponse

from ..cases.csv_export import csv_output_generator
from ..simplified.csv_export import SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT
from ..simplified.models import SimplifiedCase


def download_equality_body_cases(
    cases: QuerySet[SimplifiedCase],
    filename: str = "enforcement_body_cases.csv",
) -> StreamingHttpResponse:
    """Given a Case queryset, download the data in csv format for equality body"""
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
            equality_body_csv=True,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
