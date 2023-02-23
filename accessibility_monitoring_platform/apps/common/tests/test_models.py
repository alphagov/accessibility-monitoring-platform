"""
Tests for common models
"""
import pytest

from ..models import Event

CHANGED_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1a\\", \\"field2\\": \\"value2\\"}}]"
}"""
CHANGED_FIELD_OLD: str = {"field1": "value1", "field2": "value2"}
CHANGED_FIELD_NEW: str = {"field1": "value1a", "field2": "value2"}
CHANGED_FIELD_DIFF: str = {"field1": "value1 -> value1a"}

CREATE_ROW_VALUE: str = """{
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]"
}"""
CREATE_ROW_OLD: str = ""
CREATE_ROW_NEW: str = {"field1": "value1", "field2": "value2"}

ADD_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]"
}"""
ADD_FIELD_OLD: str = {"field1": "value1"}
ADD_FIELD_NEW: str = {"field1": "value1", "field2": "value2"}
ADD_FIELD_DIFF: str = {"field2": "-> value2"}

REMOVE_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\"}}]"
}"""
REMOVE_FIELD_OLD: str = {"field1": "value1", "field2": "value2"}
REMOVE_FIELD_NEW: str = {"field1": "value1"}
REMOVE_FIELD_DIFF: str = {"field2": "value2 ->"}


@pytest.mark.parametrize(
    "value, old, new, diff",
    [
        (CHANGED_FIELD_VALUE, CHANGED_FIELD_OLD, CHANGED_FIELD_NEW, CHANGED_FIELD_DIFF),
        (CREATE_ROW_VALUE, CREATE_ROW_OLD, CREATE_ROW_NEW, CREATE_ROW_NEW),
        (ADD_FIELD_VALUE, ADD_FIELD_OLD, ADD_FIELD_NEW, ADD_FIELD_DIFF),
        (REMOVE_FIELD_VALUE, REMOVE_FIELD_OLD, REMOVE_FIELD_NEW, REMOVE_FIELD_DIFF),
    ],
)
def test_event_diff(value, old, new, diff):
    """Test event diff contains expected value"""
    event = Event(value=value)

    assert event.old == old  # Old field values
    assert event.new == new  # New field values
    assert event.diff == diff  # Changed field value
