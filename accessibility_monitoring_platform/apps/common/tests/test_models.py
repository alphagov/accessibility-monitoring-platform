"""
Tests for common models
"""

import pytest

from ..models import Event, IssueReport

CHANGED_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1a\\", \\"field2\\": \\"value2\\"}}]"
}"""
CHANGED_FIELD_OLD_FIELDS: str = {"field1": "value1", "field2": "value2"}
CHANGED_FIELD_NEW_FIELDS: str = {"field1": "value1a", "field2": "value2"}
CHANGED_FIELD_DIFF: str = {"field1": "value1 -> value1a"}

CREATE_ROW_VALUE: str = """{
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]"
}"""
CREATE_ROW_OLD_FIELDS: str = ""
CREATE_ROW_NEW_FIELDS: str = {"field1": "value1", "field2": "value2"}

ADD_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]"
}"""
ADD_FIELD_OLD_FIELDS: str = {"field1": "value1"}
ADD_FIELD_NEW_FIELDS: str = {"field1": "value1", "field2": "value2"}
ADD_FIELD_DIFF: str = {"field2": "-> value2"}

REMOVE_FIELD_VALUE: str = """{
    "old": "[{\\"fields\\": {\\"field1\\": \\"value1\\", \\"field2\\": \\"value2\\"}}]",
    "new": "[{\\"fields\\": {\\"field1\\": \\"value1\\"}}]"
}"""
REMOVE_FIELD_OLD_FIELDS: str = {"field1": "value1", "field2": "value2"}
REMOVE_FIELD_NEW_FIELDS: str = {"field1": "value1"}
REMOVE_FIELD_DIFF: str = {"field2": "value2 ->"}


@pytest.mark.parametrize(
    "value, old_fields, new_fields, diff",
    [
        (
            CHANGED_FIELD_VALUE,
            CHANGED_FIELD_OLD_FIELDS,
            CHANGED_FIELD_NEW_FIELDS,
            CHANGED_FIELD_DIFF,
        ),
        (
            CREATE_ROW_VALUE,
            CREATE_ROW_OLD_FIELDS,
            CREATE_ROW_NEW_FIELDS,
            CREATE_ROW_NEW_FIELDS,
        ),
        (ADD_FIELD_VALUE, ADD_FIELD_OLD_FIELDS, ADD_FIELD_NEW_FIELDS, ADD_FIELD_DIFF),
        (
            REMOVE_FIELD_VALUE,
            REMOVE_FIELD_OLD_FIELDS,
            REMOVE_FIELD_NEW_FIELDS,
            REMOVE_FIELD_DIFF,
        ),
    ],
)
def test_event_diff(value, old_fields, new_fields, diff):
    """Test event diff contains expected value"""
    event = Event(value=value)

    assert event.old_fields == old_fields  # Old field values
    assert event.new_fields == new_fields  # New field values
    assert event.diff == diff  # Changed field values


def test_issue_number_incremented_on_creation(admin_user):
    """Test that each new issue_report gets the next issue_report_number"""
    issue_report_one: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_one.issue_number == 1

    issue_report_two: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_two.issue_number == 2
