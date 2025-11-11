"""
Test for send_reminders_email command which should only email the users on a Monday.
"""

import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command

MONDAY: datetime = datetime(2025, 11, 10, 2, 0, 0, tzinfo=timezone.utc)
TUESDAY: datetime = datetime(2025, 11, 11, 2, 0, 0, tzinfo=timezone.utc)
WEDNESDAY: datetime = datetime(2025, 11, 12, 2, 0, 0, tzinfo=timezone.utc)
THURSDAY: datetime = datetime(2025, 11, 13, 2, 0, 0, tzinfo=timezone.utc)
FRIDAY: datetime = datetime(2025, 11, 14, 2, 0, 0, tzinfo=timezone.utc)
SATURDAY: datetime = datetime(2025, 11, 15, 2, 0, 0, tzinfo=timezone.utc)
SUNDAY: datetime = datetime(2025, 11, 16, 2, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "call_time, expected_to_call",
    [
        (MONDAY, True),
        (TUESDAY, False),
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
    with patch(
        "django.utils.timezone.now",
        Mock(return_value=call_time),
    ):
        with patch(
            "accessibility_monitoring_platform.apps.notifications.management.commands.send_reminders_email.email_all_specialists_all_detailed_reminders_due",
            mock_email_all_specialists_all_detailed_reminders_due,
        ):
            call_command("send_reminders_email")

    if expected_to_call is True:
        mock_email_all_specialists_all_detailed_reminders_due.assert_called_once()
    else:
        mock_email_all_specialists_all_detailed_reminders_due.assert_not_called()
