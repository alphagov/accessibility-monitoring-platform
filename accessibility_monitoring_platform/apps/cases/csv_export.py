"""Utility functions for CSV exports"""

import copy
import csv
from typing import Any, Generator

from django.db.models import QuerySet
from django.urls import reverse

from ..audits.models import Audit
from ..common.csv_export import CSVColumn, EqualityBodyCSVColumn, format_model_field
from ..detailed.models import Contact as DetailedContact
from ..detailed.models import DetailedCase
from ..reports.models import Report
from ..simplified.csv_export import (
    CONTACT_DETAILS_COLUMN_HEADER,
    SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    format_simplified_contacts,
)
from ..simplified.models import CaseCompliance, CaseStatus
from ..simplified.models import Contact as SimplifiedContact
from ..simplified.models import SimplifiedCase

DOWNLOAD_CASES_CHUNK_SIZE: int = 500


def populate_equality_body_columns(
    case: DetailedCase | SimplifiedCase,
    column_definitions: list[CSVColumn] = SIMPLIFIED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
) -> list[EqualityBodyCSVColumn]:
    """
    Collect data for a case to export to the equality body
    """
    contact_details: str = (
        format_simplified_contacts(contacts=case.contacts)
        if isinstance(case, SimplifiedCase)
        else case.equality_body_export_contact_details
    )
    source_instances: dict = {
        SimplifiedCase: case if isinstance(case, SimplifiedCase) else None,
        DetailedCase: case if isinstance(case, DetailedCase) else None,
        Audit: case.audit if hasattr(case, "audit") else None,
        CaseCompliance: case.compliance if hasattr(case, "compliance") else None,
        Report: case.report if hasattr(case, "report") else None,
    }
    columns: list[EqualityBodyCSVColumn] = copy.deepcopy(column_definitions)
    for column in columns:
        source_instance: (
            Audit | DetailedCase | SimplifiedCase | CaseCompliance | Report | None
        ) = source_instances.get(column.source_class)
        edit_url_instance: (
            Audit | DetailedCase | SimplifiedCase | CaseCompliance | Report | None
        ) = source_instances.get(column.edit_url_class)
        if column.column_header == CONTACT_DETAILS_COLUMN_HEADER:
            column.formatted_data = contact_details
        else:
            column.formatted_data = format_model_field(
                source_instance=source_instance, column=column
            )
        if column.edit_url_name is not None and edit_url_instance is not None:
            column.edit_url = reverse(
                column.edit_url_name, kwargs={"pk": edit_url_instance.id}
            )
            if column.edit_url_anchor:
                column.edit_url += f"#{column.edit_url_anchor}"
    return columns


def populate_csv_columns(
    case: DetailedCase | SimplifiedCase, column_definitions: list[CSVColumn]
) -> list[CSVColumn]:
    """
    Collect data for a case to export
    """
    source_instances: dict = {
        SimplifiedCase: case if isinstance(case, SimplifiedCase) else None,
        DetailedCase: case if isinstance(case, DetailedCase) else None,
        CaseCompliance: case.compliance if hasattr(case, "compliance") else None,
        CaseStatus: case.status,
        SimplifiedContact: (
            case.contact_set.filter(is_deleted=False).first()
            if isinstance(case, SimplifiedCase)
            else None
        ),
        DetailedContact: (
            case.contact_set.filter(is_deleted=False).first()
            if isinstance(case, DetailedCase)
            else None
        ),
    }
    columns: list[CSVColumn] = copy.deepcopy(column_definitions)
    for column in columns:
        source_instance: (
            DetailedCase
            | SimplifiedCase
            | CaseCompliance
            | CaseStatus
            | SimplifiedContact
            | None
        ) = source_instances.get(column.source_class)
        column.formatted_data = format_model_field(
            source_instance=source_instance, column=column
        )
    return columns


def csv_output_generator(
    cases: QuerySet[SimplifiedCase] | QuerySet[DetailedCase],
    columns_for_export: list[CSVColumn],
    equality_body_csv: bool = False,
) -> Generator[str, None, None]:
    """
    Generate a series of strings containing the content for a CSV streaming response
    """

    class DummyFile:
        def write(self, value_to_write):
            return value_to_write

    writer: Any = csv.writer(DummyFile())
    column_row: list[str] = [column.column_header for column in columns_for_export]

    output: str = writer.writerow(column_row)

    for counter, case in enumerate(cases):
        if equality_body_csv is True:
            case_columns: list[EqualityBodyCSVColumn] = populate_equality_body_columns(
                case=case.get_case()
            )
        else:
            case_columns: list[CSVColumn] = populate_csv_columns(
                case=case.get_case(), column_definitions=columns_for_export
            )
        row = [column.formatted_data for column in case_columns]
        output += writer.writerow(row)
        if counter % DOWNLOAD_CASES_CHUNK_SIZE == 0:
            yield output
            output = ""
    if output:
        yield output
