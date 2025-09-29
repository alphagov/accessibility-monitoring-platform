"""Test CSV export functions of simplified app"""

from datetime import date

import pytest

from ...simplified.models import SimplifiedCase
from ..csv_export import CSVColumn, EqualityBodyCSVColumn, format_model_field


def test_format_model_field_with_no_data():
    """
    Test that format_model_field returns empty string if no model instance
    """
    assert (
        format_model_field(
            source_instance=None,
            column=CSVColumn(
                column_header="A", source_class=SimplifiedCase, source_attr="a"
            ),
        )
        == ""
    )


@pytest.mark.parametrize(
    "column, case_value, expected_formatted_value",
    [
        (
            CSVColumn(
                column_header="Test type",
                source_class=SimplifiedCase,
                source_attr="test_type",
            ),
            "simplified",
            "Simplified",
        ),
        (
            CSVColumn(
                column_header="Report sent on",
                source_class=SimplifiedCase,
                source_attr="report_sent_date",
            ),
            date(2020, 12, 31),
            "31/12/2020",
        ),
        (
            CSVColumn(
                column_header="Enforcement recommendation",
                source_class=SimplifiedCase,
                source_attr="recommendation_for_enforcement",
            ),
            "no-further-action",
            "No further action",
        ),
        (
            CSVColumn(
                column_header="Which equality body will check the case",
                source_class=SimplifiedCase,
                source_attr="enforcement_body",
            ),
            "ehrc",
            "EHRC",
        ),
    ],
)
def test_format_model_field(column, case_value, expected_formatted_value):
    """Test that model fields are formatted correctly"""
    simplified_case: SimplifiedCase = SimplifiedCase()
    setattr(simplified_case, column.source_attr, case_value)
    assert expected_formatted_value == format_model_field(
        source_instance=simplified_case, column=column
    )


def test_required_data_missing():
    """Test equality body CSV column required_data_missing"""
    equality_body_csv_column: EqualityBodyCSVColumn = EqualityBodyCSVColumn(
        column_header="A", source_class=SimplifiedCase, source_attr="a"
    )

    assert equality_body_csv_column.required_data_missing is False

    equality_body_csv_column.required = True

    assert equality_body_csv_column.required_data_missing is True

    equality_body_csv_column.formatted_data = None

    assert equality_body_csv_column.required_data_missing is True

    equality_body_csv_column.formatted_data = "formatted string"

    assert equality_body_csv_column.required_data_missing is False
