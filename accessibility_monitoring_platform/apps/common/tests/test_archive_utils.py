"""Test utilities used to archive data"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

import pytest

from ..archive_utils import build_field, build_section


@dataclass
class MockModel:
    date_field: date | None = None
    datetime_field: datetime | None = None
    link_field: str | None = None
    string_field: str | None = None
    string_with_display_field: str | None = None
    markdown_field: str | None = None

    def get_string_with_display_field_display(self):
        return self.string_with_display_field.capitalize()


def test_build_section_without_subsections():
    """Test building a section without subsections"""
    assert build_section(name="Section name", complete_date=None, fields=[]) == {
        "complete": None,
        "fields": [],
        "name": "Section name",
        "subsections": None,
    }


def test_build_section_with_subsections():
    """Test building a section with subsections"""
    assert build_section(
        name="Section name",
        complete_date=date(2023, 4, 1),
        fields=["field"],
        subsections=["subsection"],
    ) == {
        "complete": "2023-04-01",
        "fields": ["field"],
        "name": "Section name",
        "subsections": ["subsection"],
    }


def test_build_field_date():
    """Test building a date field"""
    mock_model: MockModel = MockModel(date_field=date(2020, 2, 28))

    assert build_field(mock_model, field_name="date_field", label="Date label") == {
        "label": "Date label",
        "name": "date_field",
        "data_type": "date",
        "value": "2020-02-28",
        "display_value": "28 February 2020",
    }


def test_build_field_datetime():
    """Test building a datetime field"""
    mock_model: MockModel = MockModel(
        datetime_field=datetime(2020, 2, 28, 12, 0, 1, 0, timezone.utc)
    )

    assert build_field(
        mock_model, field_name="datetime_field", label="Datetime label"
    ) == {
        "label": "Datetime label",
        "name": "datetime_field",
        "data_type": "datetime",
        "value": "2020-02-28T12:00:01+00:00",
        "display_value": "28 February 2020 12:00pm",
    }


def test_build_field_link():
    """Test building a URL link field"""
    mock_model: MockModel = MockModel(link_field="https://example.com")

    assert build_field(
        mock_model,
        field_name="link_field",
        label="Link label",
        data_type="link",
        display_value="example.com",
    ) == {
        "label": "Link label",
        "name": "link_field",
        "data_type": "link",
        "value": "https://example.com",
        "display_value": "example.com",
    }


def test_build_field_str():
    """Test building a string field"""
    mock_model: MockModel = MockModel(string_field="string")

    assert build_field(mock_model, field_name="string_field", label="String label") == {
        "label": "String label",
        "name": "string_field",
        "data_type": "str",
        "value": "string",
        "display_value": None,
    }


def test_build_field_str_with_display():
    """Test building a string field with display function"""
    mock_model: MockModel = MockModel(string_with_display_field="string with display")

    assert build_field(
        mock_model,
        field_name="string_with_display_field",
        label="String with display label",
    ) == {
        "label": "String with display label",
        "name": "string_with_display_field",
        "data_type": "str",
        "value": "string with display",
        "display_value": "String with display",
    }


def test_build_field_markdown():
    """Test building a markdown field"""
    mock_model: MockModel = MockModel(markdown_field="# Markdown")

    assert build_field(
        mock_model,
        field_name="markdown_field",
        label="Markdown label",
        data_type="markdown",
    ) == {
        "label": "Markdown label",
        "name": "markdown_field",
        "data_type": "markdown",
        "value": "# Markdown",
        "display_value": None,
    }


def test_unknown_data_type_raises_exception():
    """
    Test that archiving data with an unexpected data type raises an exception
    """
    mock_model: MockModel = MockModel(string_field="string")

    with pytest.raises(ValueError) as excinfo:
        build_field(
            mock_model, field_name="string_field", label="", data_type="unknown"
        )

    assert "Unknown data_type" in str(excinfo.value)
