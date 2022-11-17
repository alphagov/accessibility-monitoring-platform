"""
Test - common utility functions
"""
import pytest
from unittest.mock import patch

from typing import Dict, List, Union
from datetime import datetime

from ..metrics import (
    calculate_current_month_progress,
    build_yearly_metric_chart,
    build_x_axis_labels,
    build_cases_y_axis_labels,
    calculate_x_axis_position_from_month,
    Y_AXIS_LABELS_100,
    Y_AXIS_LABELS_250,
)

METRIC_LABEL: str = "Metric label"


@pytest.mark.parametrize(
    "day_of_month, number_done_this_month, number_done_last_month, expected_metric",
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
    number_done_this_month,
    number_done_last_month,
    expected_metric,
):
    """
    Test calculation of progress through current month
    """
    mock_timezone.now.return_value = datetime(2022, 12, day_of_month)
    expected_metric["label"] = METRIC_LABEL
    expected_metric["number_done_this_month"] = number_done_this_month
    expected_metric["number_done_last_month"] = number_done_last_month

    assert expected_metric == calculate_current_month_progress(
        label=METRIC_LABEL,
        number_done_this_month=number_done_this_month,
        number_done_last_month=number_done_last_month,
    )


def test_build_yearly_metric_chart():
    """
    Test building of yearly metric data for line chart
    """
    label: str = "Label"
    all_table_rows: List[Dict[str, Union[datetime, int]]] = [
        {"month_date": datetime(2021, 11, 1), "count": 42},
        {"month_date": datetime(2021, 12, 1), "count": 54},
        {"month_date": datetime(2022, 1, 1), "count": 45},
        {"month_date": datetime(2022, 2, 1), "count": 20},
        {"month_date": datetime(2022, 3, 1), "count": 64},
        {"month_date": datetime(2022, 4, 1), "count": 22},
        {"month_date": datetime(2022, 5, 1), "count": 44},
        {"month_date": datetime(2022, 6, 1), "count": 42},
        {"month_date": datetime(2022, 7, 1), "count": 45},
        {"month_date": datetime(2022, 8, 1), "count": 49},
        {"month_date": datetime(2022, 9, 1), "count": 52},
        {"month_date": datetime(2022, 10, 1), "count": 54},
        {"month_date": datetime(2022, 11, 1), "count": 8},
    ]
    assert build_yearly_metric_chart(label=label, all_table_rows=all_table_rows) == {
        "label": label,
        "all_table_rows": all_table_rows,
        "previous_month_rows": all_table_rows[:-1],
        "current_month_rows": all_table_rows[-2:],
        "graph_height": 250,
        "graph_width": 600,
        "chart_height": 300,
        "chart_width": 750,
        "x_axis_tick_y2": 260,
        "x_axis_label_y": 275,
        "y_axis_labels": Y_AXIS_LABELS_100,
    }


@pytest.mark.parametrize(
    "month,expected_result",
    [
        (
            11,
            [
                {"label": "Nov", "x": 0},
                {"label": "Dec", "x": 50},
                {"label": "Jan", "x": 100, "label_line_2": 2022},
                {"label": "Feb", "x": 150},
                {"label": "Mar", "x": 200},
                {"label": "Apr", "x": 250},
                {"label": "May", "x": 300},
                {"label": "Jun", "x": 350},
                {"label": "Jul", "x": 400},
                {"label": "Aug", "x": 450},
                {"label": "Sep", "x": 500},
                {"label": "Oct", "x": 550},
                {"label": "Nov", "x": 600},
            ],
        ),
        (
            1,
            [
                {"label": "Jan", "x": 0, "label_line_2": 2021},
                {"label": "Feb", "x": 50},
                {"label": "Mar", "x": 100},
                {"label": "Apr", "x": 150},
                {"label": "May", "x": 200},
                {"label": "Jun", "x": 250},
                {"label": "Jul", "x": 300},
                {"label": "Aug", "x": 350},
                {"label": "Sep", "x": 400},
                {"label": "Oct", "x": 450},
                {"label": "Nov", "x": 500},
                {"label": "Dec", "x": 550},
                {"label": "Jan", "x": 600, "label_line_2": 2022},
            ],
        ),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_build_x_axis_labels(mock_timezone, month, expected_result):
    """
    Test building of x-axis labels for charts
    """
    mock_timezone.now.return_value = datetime(2022, month, 1)
    assert build_x_axis_labels() == expected_result


@pytest.mark.parametrize(
    "max_value,expected_result",
    [
        (99, Y_AXIS_LABELS_100),
        (101, Y_AXIS_LABELS_250),
    ],
)
def test_build_cases_y_axis_labels(max_value, expected_result):
    """
    Test building of y-axis labels for cases charts
    """
    assert build_cases_y_axis_labels(max_value=max_value) == expected_result


@pytest.mark.parametrize(
    "now,metric_date,expected_result",
    [
        (datetime(2022, 11, 15), datetime(2022, 11, 1), 600),
        (datetime(2022, 1, 15), datetime(2021, 11, 1), 500),
        (datetime(2022, 1, 15), datetime(2021, 1, 1), 0),
    ],
)
def test_calculate_x_axis_position_from_month(now, metric_date, expected_result):
    """
    Test metric's position on the x-axis of a chart is calculated correctly.
    """
    assert (
        calculate_x_axis_position_from_month(now=now, metric_date=metric_date)
        == expected_result
    )
