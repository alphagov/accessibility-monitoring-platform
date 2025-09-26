"""Utility functions for CSV exports"""

from django.db.models import QuerySet
from django.http import StreamingHttpResponse

from ..cases.csv_export import csv_output_generator
from ..cases.models import BaseCase
from ..detailed.csv_export import (
    DETAILED_CASE_COLUMNS_FOR_EXPORT,
    DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..detailed.models import DetailedCase
from ..simplified.csv_export import (
    SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from ..simplified.models import SimplifiedCase

DOWNLOAD_CASES_CHUNK_SIZE: int = 500


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


def download_simplified_cases(
    simplified_cases: QuerySet[SimplifiedCase], filename: str = "cases.csv"
) -> StreamingHttpResponse:
    """Given a Case queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=simplified_cases,
            columns_for_export=SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_detailed_cases(
    detailed_cases: QuerySet[BaseCase], filename: str = "detailed_cases.csv"
) -> StreamingHttpResponse:
    """Given a Case queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=detailed_cases,
            columns_for_export=DETAILED_CASE_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_simplified_feedback_survey_cases(
    cases: QuerySet[SimplifiedCase],
    filename: str = "simplified_feedback_survey_cases.csv",
) -> StreamingHttpResponse:
    """Given a Case queryset, download the feedback survey data in csv format"""
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_detailed_feedback_survey_cases(
    cases: QuerySet[DetailedCase], filename: str = "detailed_feedback_survey_cases.csv"
) -> StreamingHttpResponse:
    """Given a Case queryset, download the feedback survey data in csv format"""
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
