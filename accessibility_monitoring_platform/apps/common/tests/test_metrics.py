"""
Test - common utility functions
"""
import pytest
from unittest.mock import patch

from datetime import datetime

from ..metrics import (
    calculate_current_month_progress,
)

METRIC_LABEL: str = "Metric label"


@pytest.mark.parametrize(
    "day_of_month, this_month_value, last_month_value, expected_metric",
    [
        (
            31,
            15,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "under",
            },
        ),
        (
            31,
            45,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            1,
            5,
            30,
            {
                "expected_progress_difference": 416,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            31,
            45,
            0,
            {},
        ),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_calculate_current_month_progress(
    mock_timezone,
    day_of_month,
    this_month_value,
    last_month_value,
    expected_metric,
):
    """
    Test calculation of progress through current month
    """
    mock_timezone.now.return_value = datetime(2022, 12, day_of_month)
    expected_metric["label"] = METRIC_LABEL
    expected_metric["this_month_value"] = this_month_value
    expected_metric["last_month_value"] = last_month_value

    assert expected_metric == calculate_current_month_progress(
        label=METRIC_LABEL,
        this_month_value=this_month_value,
        last_month_value=last_month_value,
    )
