import pytest

from dataclasses import dataclass
from typing import Dict

from ..utils import get_sent_date


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: Dict[str, str]


@pytest.mark.parametrize(
    "date_on_form, date_on_db, expected_date",
    [
        ("form_date", "db_date", "db_date"),
        (None, "db_date", None),
        ("form_date", None, "form_date"),
    ],
)
def test_get_sent_date(date_on_form, date_on_db, expected_date):
    mock_form: MockForm = MockForm(cleaned_data={"sent_date": date_on_form})
    mock_case: MockCase = MockCase(sent_date=date_on_db)

    assert (
        get_sent_date(
            form=mock_form, case_from_db=mock_case, sent_date_name="sent_date"
        )
        == expected_date
    )
