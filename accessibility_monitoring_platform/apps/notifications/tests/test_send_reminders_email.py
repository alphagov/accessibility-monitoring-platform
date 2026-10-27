"""
Test for send_reminders_email command which should only email the users on a Monday.
"""

import os
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

MONDAY: datetime = datetime(2025, 11, 10, 2, 0, 0, tzinfo=UTC)
TUESDAY: datetime = datetime(2025, 11, 11, 2, 0, 0, tzinfo=UTC)
WEDNESDAY: datetime = datetime(2025, 11, 12, 2, 0, 0, tzinfo=UTC)
THURSDAY: datetime = datetime(2025, 11, 13, 2, 0, 0, tzinfo=UTC)
FRIDAY: datetime = datetime(2025, 11, 14, 2, 0, 0, tzinfo=UTC)
SATURDAY: datetime = datetime(2025, 11, 15, 2, 0, 0, tzinfo=UTC)
SUNDAY: datetime = datetime(2025, 11, 16, 2, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "call_time, expected_to_call",
    [
        (MONDAY, True),
        (TUESDAY, False),
        (WEDNESDAY, False),
        (THURSDAY, False),
        (FRIDAY, False),
        (SATURDAY, False),
        (SUNDAY, False),
    ],
)
@pytest.mark.django_db
def test_send_reminders_email_only_called_monday(call_time, expected_to_call):
    """Test send_reminders_email only calls init_int_test_data can be called"""
    os.environ["COPILOT_ENVIRONMENT_NAME"] = "prodenv"
    mock_email_all_specialists_all_detailed_reminders_due: Mock = Mock()
    with (
        patch("django.utils.timezone.now", Mock(return_value=call_time)),
        patch(
            "accessibility_monitoring_platform.apps.notifications.management.commands.send_reminders_email.email_all_specialists_all_detailed_reminders_due",
            mock_email_all_specialists_all_detailed_reminders_due,
        ),
    ):
        call_command("send_reminders_email")

    if expected_to_call is True:
        mock_email_all_specialists_all_detailed_reminders_due.assert_called_once()
    else:
        mock_email_all_specialists_all_detailed_reminders_due.assert_not_called()
