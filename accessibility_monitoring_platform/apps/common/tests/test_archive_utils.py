from dataclasses import dataclass
from datetime import date, datetime

from ..archive_utils import build_field, build_section


@dataclass
class MockModel:
    datetime_field: datetime


def test_build_section():
    assert build_section(
        name="Section name", complete_date=date(2023, 4, 1), fields=[]
    ) == {
        "complete": "2023-04-01",
        "fields": [],
        "name": "Section name",
        "subsections": None,
    }


def test_build_field_date():
    mock_model: MockModel = MockModel(datetime_field=datetime(2020, 2, 28, 12, 0, 1))

    assert build_field(
        mock_model, field_name="datetime_field", label="Datetime label"
    ) == {
        "label": "Datetime label",
        "name": "datetime_field",
        "data_type": "datetime",
        "value": "2020-02-28T12:00:01",
        "display_value": "28 February 2020 12:00PM",
    }
