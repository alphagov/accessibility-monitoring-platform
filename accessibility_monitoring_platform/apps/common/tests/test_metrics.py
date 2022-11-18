"""
Test - common utility functions
"""
import pytest
from unittest.mock import patch

from typing import List
from datetime import datetime, timezone

from ..metrics import (
    TimeseriesData,
    ChartAxisTick,
    Point,
    Polyline,
    TimeseriesLineChart,
    calculate_current_month_progress,
    build_yearly_metric_chart,
    build_13_month_x_axis,
    build_cases_y_axis,
    calculate_x_position_from_metric_date,
    Y_AXIS_100,
    Y_AXIS_250,
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
    data_series: List[TimeseriesData] = [
        TimeseriesData(datetime=datetime(2021, 11, 1), value=42),
        TimeseriesData(datetime=datetime(2021, 12, 1), value=54),
        TimeseriesData(datetime=datetime(2022, 1, 1), value=45),
        TimeseriesData(datetime=datetime(2022, 2, 1), value=20),
        TimeseriesData(datetime=datetime(2022, 3, 1), value=64),
        TimeseriesData(datetime=datetime(2022, 4, 1), value=22),
        TimeseriesData(datetime=datetime(2022, 5, 1), value=44),
        TimeseriesData(datetime=datetime(2022, 6, 1), value=42),
        TimeseriesData(datetime=datetime(2022, 7, 1), value=45),
        TimeseriesData(datetime=datetime(2022, 8, 1), value=49),
        TimeseriesData(datetime=datetime(2022, 9, 1), value=52),
        TimeseriesData(datetime=datetime(2022, 10, 1), value=54),
        TimeseriesData(datetime=datetime(2022, 11, 1), value=8),
    ]
    assert build_yearly_metric_chart(data_series=[data_series]) == TimeseriesLineChart(
        x_axis=[
            ChartAxisTick(
                value=datetime(2021, 11, 1, 0, 0, tzinfo=timezone.utc),
                label="Nov",
                x_position=0,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 12, 1, 0, 0, tzinfo=timezone.utc),
                label="Dec",
                x_position=50,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
                label="Jan",
                x_position=100,
                y_position=275,
                label_line_2="2021",
            ),
            ChartAxisTick(
                value=datetime(2021, 2, 1, 0, 0, tzinfo=timezone.utc),
                label="Feb",
                x_position=150,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 3, 1, 0, 0, tzinfo=timezone.utc),
                label="Mar",
                x_position=200,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 4, 1, 0, 0, tzinfo=timezone.utc),
                label="Apr",
                x_position=250,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 5, 1, 0, 0, tzinfo=timezone.utc),
                label="May",
                x_position=300,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 6, 1, 0, 0, tzinfo=timezone.utc),
                label="Jun",
                x_position=350,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 7, 1, 0, 0, tzinfo=timezone.utc),
                label="Jul",
                x_position=400,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 8, 1, 0, 0, tzinfo=timezone.utc),
                label="Aug",
                x_position=450,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 9, 1, 0, 0, tzinfo=timezone.utc),
                label="Sep",
                x_position=500,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 10, 1, 0, 0, tzinfo=timezone.utc),
                label="Oct",
                x_position=550,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2021, 11, 1, 0, 0, tzinfo=timezone.utc),
                label="Nov",
                x_position=600,
                y_position=275,
                label_line_2="",
            ),
        ],
        y_axis=[
            ChartAxisTick(
                value=100, label="100", x_position=0, y_position=0, label_line_2=""
            ),
            ChartAxisTick(
                value=80, label="80", x_position=0, y_position=50, label_line_2=""
            ),
            ChartAxisTick(
                value=60, label="60", x_position=0, y_position=100, label_line_2=""
            ),
            ChartAxisTick(
                value=40, label="40", x_position=0, y_position=150, label_line_2=""
            ),
            ChartAxisTick(
                value=20, label="20", x_position=0, y_position=200, label_line_2=""
            ),
            ChartAxisTick(
                value=0, label="0", x_position=0, y_position=250, label_line_2=""
            ),
        ],
        polylines=[
            Polyline(
                points=[
                    Point(x_position=0, y_position=145),
                    Point(x_position=50, y_position=115),
                    Point(x_position=100, y_position=137),
                    Point(x_position=150, y_position=200),
                    Point(x_position=200, y_position=90),
                    Point(x_position=250, y_position=195),
                    Point(x_position=300, y_position=140),
                    Point(x_position=350, y_position=145),
                    Point(x_position=400, y_position=137),
                    Point(x_position=450, y_position=127),
                    Point(x_position=500, y_position=120),
                    Point(x_position=550, y_position=115),
                ],
                stroke_dasharray="",
                stroke="#1d70b8",
            ),
            Polyline(
                points=[
                    Point(x_position=550, y_position=115),
                    Point(x_position=600, y_position=230),
                ],
                stroke_dasharray="5",
                stroke="#1d70b8",
            ),
        ],
        graph_height=250,
        graph_width=600,
        chart_height=300,
        chart_width=750,
        x_axis_tick_y2=260,
    )


@pytest.mark.parametrize(
    "month,expected_result",
    [
        (
            11,
            [
                ChartAxisTick(
                    value=datetime(2021, 11, 1, 0, 0, tzinfo=timezone.utc),
                    label="Nov",
                    x_position=0,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 12, 1, 0, 0, tzinfo=timezone.utc),
                    label="Dec",
                    x_position=50,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jan",
                    x_position=100,
                    y_position=275,
                    label_line_2="2021",
                ),
                ChartAxisTick(
                    value=datetime(2021, 2, 1, 0, 0, tzinfo=timezone.utc),
                    label="Feb",
                    x_position=150,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 3, 1, 0, 0, tzinfo=timezone.utc),
                    label="Mar",
                    x_position=200,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 4, 1, 0, 0, tzinfo=timezone.utc),
                    label="Apr",
                    x_position=250,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 5, 1, 0, 0, tzinfo=timezone.utc),
                    label="May",
                    x_position=300,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 6, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jun",
                    x_position=350,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 7, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jul",
                    x_position=400,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 8, 1, 0, 0, tzinfo=timezone.utc),
                    label="Aug",
                    x_position=450,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 9, 1, 0, 0, tzinfo=timezone.utc),
                    label="Sep",
                    x_position=500,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 10, 1, 0, 0, tzinfo=timezone.utc),
                    label="Oct",
                    x_position=550,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 11, 1, 0, 0, tzinfo=timezone.utc),
                    label="Nov",
                    x_position=600,
                    y_position=275,
                    label_line_2="",
                ),
            ],
        ),
        (
            1,
            [
                ChartAxisTick(
                    value=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jan",
                    x_position=0,
                    y_position=275,
                    label_line_2="2021",
                ),
                ChartAxisTick(
                    value=datetime(2021, 2, 1, 0, 0, tzinfo=timezone.utc),
                    label="Feb",
                    x_position=50,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 3, 1, 0, 0, tzinfo=timezone.utc),
                    label="Mar",
                    x_position=100,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 4, 1, 0, 0, tzinfo=timezone.utc),
                    label="Apr",
                    x_position=150,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 5, 1, 0, 0, tzinfo=timezone.utc),
                    label="May",
                    x_position=200,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 6, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jun",
                    x_position=250,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 7, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jul",
                    x_position=300,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 8, 1, 0, 0, tzinfo=timezone.utc),
                    label="Aug",
                    x_position=350,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 9, 1, 0, 0, tzinfo=timezone.utc),
                    label="Sep",
                    x_position=400,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 10, 1, 0, 0, tzinfo=timezone.utc),
                    label="Oct",
                    x_position=450,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 11, 1, 0, 0, tzinfo=timezone.utc),
                    label="Nov",
                    x_position=500,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 12, 1, 0, 0, tzinfo=timezone.utc),
                    label="Dec",
                    x_position=550,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jan",
                    x_position=600,
                    y_position=275,
                    label_line_2="2021",
                ),
            ],
        ),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_build_13_month_x_axis_labels(mock_timezone, month, expected_result):
    """
    Test building of x-axis labels for charts
    """
    mock_timezone.now.return_value = datetime(2022, month, 1)
    mock_timezone.utc = timezone.utc
    assert build_13_month_x_axis() == expected_result


@pytest.mark.parametrize(
    "max_value,expected_result",
    [
        (99, Y_AXIS_100),
        (101, Y_AXIS_250),
    ],
)
def test_build_cases_y_axis_labels(max_value, expected_result):
    """
    Test building of y-axis labels for cases charts
    """
    assert build_cases_y_axis(max_value=max_value) == expected_result


@pytest.mark.parametrize(
    "now,metric_date,expected_result",
    [
        (datetime(2022, 11, 15), datetime(2022, 11, 1), 600),
        (datetime(2022, 1, 15), datetime(2021, 11, 1), 500),
        (datetime(2022, 1, 15), datetime(2021, 1, 1), 0),
    ],
)
def test_calculate_x_position_from_metric_date(now, metric_date, expected_result):
    """
    Test metric's position on the x-axis of a chart is calculated correctly.
    """
    assert (
        calculate_x_position_from_metric_date(now=now, metric_date=metric_date)
        == expected_result
    )
