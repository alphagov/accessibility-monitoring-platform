"""
Test - common utility functions
"""
import pytest
from unittest.mock import patch

from datetime import datetime, timezone

from ..chart import (
    Timeseries,
    TimeseriesDatapoint,
    ChartAxisTick,
    Point,
    Polyline,
    LineChart,
    LegendEntry,
    PolylineStroke,
    calculate_x_position_from_datapoint_datetime,
    calculate_timeseries_point,
    build_13_month_x_axis,
    build_y_axis,
    calculate_y_tick_size,
    build_yearly_metric_chart,
    get_polyline_stroke,
    Y_AXIS_RATIO,
)


@pytest.mark.parametrize(
    "now, datapoint_datetime, expected_result",
    [
        (datetime(2022, 11, 15), datetime(2022, 11, 1), 600),
        (datetime(2022, 1, 15), datetime(2021, 11, 1), 500),
        (datetime(2022, 1, 15), datetime(2021, 1, 1), 0),
    ],
)
def test_calculate_x_position_from_metric_date(
    now, datapoint_datetime, expected_result
):
    """
    Test metric's position on the x-axis of a chart is calculated correctly.
    """
    assert (
        calculate_x_position_from_datapoint_datetime(
            now=now, datapoint_datetime=datapoint_datetime
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "now, y_tick_size, datapoint, expected_result",
    [
        (
            datetime(2022, 11, 15),
            4,
            TimeseriesDatapoint(datetime=datetime(2022, 11, 1), value=13),
            Point(x_position=600, y_position=87),
        ),
        (
            datetime(2022, 11, 15),
            10,
            TimeseriesDatapoint(datetime=datetime(2022, 11, 1), value=13),
            Point(x_position=600, y_position=185),
        ),
        (
            datetime(2022, 11, 15),
            20,
            TimeseriesDatapoint(datetime=datetime(2022, 11, 1), value=13),
            Point(x_position=600, y_position=217),
        ),
        (
            datetime(2022, 11, 15),
            20,
            TimeseriesDatapoint(datetime=datetime(2022, 10, 1), value=13),
            Point(x_position=550, y_position=217),
        ),
    ],
)
def test_calculate_timeseries_point(
    now: datetime,
    y_tick_size: int,
    datapoint: TimeseriesDatapoint,
    expected_result: int,
):
    """Test position of timeseries data point is calculated correctly"""
    assert calculate_timeseries_point(now, y_tick_size, datapoint) == expected_result


@pytest.mark.parametrize(
    "month, expected_result",
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
                    value=datetime(2022, 1, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jan",
                    x_position=100,
                    y_position=275,
                    label_line_2="2022",
                ),
                ChartAxisTick(
                    value=datetime(2022, 2, 1, 0, 0, tzinfo=timezone.utc),
                    label="Feb",
                    x_position=150,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
                    label="Mar",
                    x_position=200,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 4, 1, 0, 0, tzinfo=timezone.utc),
                    label="Apr",
                    x_position=250,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 5, 1, 0, 0, tzinfo=timezone.utc),
                    label="May",
                    x_position=300,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 6, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jun",
                    x_position=350,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 7, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jul",
                    x_position=400,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 8, 1, 0, 0, tzinfo=timezone.utc),
                    label="Aug",
                    x_position=450,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 9, 1, 0, 0, tzinfo=timezone.utc),
                    label="Sep",
                    x_position=500,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 10, 1, 0, 0, tzinfo=timezone.utc),
                    label="Oct",
                    x_position=550,
                    y_position=275,
                    label_line_2="",
                ),
                ChartAxisTick(
                    value=datetime(2022, 11, 1, 0, 0, tzinfo=timezone.utc),
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
                    value=datetime(2022, 1, 1, 0, 0, tzinfo=timezone.utc),
                    label="Jan",
                    x_position=600,
                    y_position=275,
                    label_line_2="2022",
                ),
            ],
        ),
    ],
)
@patch("accessibility_monitoring_platform.apps.common.chart.timezone")
def test_build_13_month_x_axis(mock_timezone, month, expected_result):
    """
    Test building of x-axis for 13-month timeseries chart
    """
    mock_timezone.now.return_value = datetime(2022, month, 1)
    assert build_13_month_x_axis() == expected_result


@pytest.mark.parametrize(
    "max_value, y_tick_size",
    [
        (7, 2),
        (10, 2),
        (11, 4),
        (49, 10),
        (50, 10),
        (51, 20),
        (100, 20),
        (101, 40),
        (800, 200),
        (1001, 400),
    ],
)
def test_calculate_y_tick_size(max_value, y_tick_size):
    """Test nice y tick size is calculated from max value"""
    assert calculate_y_tick_size(max_value) == y_tick_size


@pytest.mark.parametrize(
    "y_tick_size, is_ratio, expected_result",
    [
        (
            20,
            False,
            [
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
        ),
        (50, True, Y_AXIS_RATIO),
    ],
)
def test_build_y_axis(y_tick_size, is_ratio, expected_result):
    """
    Test building of y-axis for charts
    """
    assert build_y_axis(y_tick_size=y_tick_size, is_ratio=is_ratio) == expected_result


@patch("accessibility_monitoring_platform.apps.common.chart.timezone")
def test_build_yearly_metric_chart(mock_timezone):
    """
    Test building of yearly metric data for line chart
    """
    mock_timezone.now.return_value = datetime(2022, 11, 10)
    timeseries: Timeseries = Timeseries(
        label="Counts",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2021, 11, 1), value=42),
            TimeseriesDatapoint(datetime=datetime(2021, 12, 1), value=54),
            TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=45),
            TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=20),
            TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=64),
            TimeseriesDatapoint(datetime=datetime(2022, 4, 1), value=22),
            TimeseriesDatapoint(datetime=datetime(2022, 5, 1), value=44),
            TimeseriesDatapoint(datetime=datetime(2022, 6, 1), value=42),
            TimeseriesDatapoint(datetime=datetime(2022, 7, 1), value=45),
            TimeseriesDatapoint(datetime=datetime(2022, 8, 1), value=49),
            TimeseriesDatapoint(datetime=datetime(2022, 9, 1), value=52),
            TimeseriesDatapoint(datetime=datetime(2022, 10, 1), value=54),
            TimeseriesDatapoint(datetime=datetime(2022, 11, 1), value=8),
        ],
    )

    assert build_yearly_metric_chart(lines=[timeseries]) == LineChart(
        legend=[
            LegendEntry(
                label="Counts",
                stroke="#1d70b8",
                stroke_dasharray="",
                label_x=30,
                label_y=-10,
                line_x1=0,
                line_x2=20,
                line_y=-15,
            )
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
                    Point(x_position=600, y_position=230),
                ],
                stroke="#1d70b8",
                stroke_dasharray="",
            )
        ],
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
                value=datetime(2022, 1, 1, 0, 0, tzinfo=timezone.utc),
                label="Jan",
                x_position=100,
                y_position=275,
                label_line_2="2022",
            ),
            ChartAxisTick(
                value=datetime(2022, 2, 1, 0, 0, tzinfo=timezone.utc),
                label="Feb",
                x_position=150,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
                label="Mar",
                x_position=200,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 4, 1, 0, 0, tzinfo=timezone.utc),
                label="Apr",
                x_position=250,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 5, 1, 0, 0, tzinfo=timezone.utc),
                label="May",
                x_position=300,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 6, 1, 0, 0, tzinfo=timezone.utc),
                label="Jun",
                x_position=350,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 7, 1, 0, 0, tzinfo=timezone.utc),
                label="Jul",
                x_position=400,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 8, 1, 0, 0, tzinfo=timezone.utc),
                label="Aug",
                x_position=450,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 9, 1, 0, 0, tzinfo=timezone.utc),
                label="Sep",
                x_position=500,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 10, 1, 0, 0, tzinfo=timezone.utc),
                label="Oct",
                x_position=550,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 11, 1, 0, 0, tzinfo=timezone.utc),
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
        graph_height=250,
        graph_width=600,
        chart_height=330,
        chart_width=680,
        x_axis_tick_y2=260,
        y_axis_tick_x1=-10,
    )


@patch("accessibility_monitoring_platform.apps.common.chart.timezone")
def test_build_yearly_metric_chart_no_current_month_data(mock_timezone):
    """
    Test building of yearly metric data for line chart with no data for current month
    """
    mock_timezone.now.return_value = datetime(2022, 11, 10)
    timeseries: Timeseries = Timeseries(
        label="Counts",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2022, 9, 1), value=52),
            TimeseriesDatapoint(datetime=datetime(2022, 10, 1), value=54),
        ],
    )

    assert build_yearly_metric_chart(lines=[timeseries]) == LineChart(
        legend=[
            LegendEntry(
                label="Counts",
                stroke="#1d70b8",
                stroke_dasharray="",
                label_x=30,
                label_y=-10,
                line_x1=0,
                line_x2=20,
                line_y=-15,
            )
        ],
        polylines=[
            Polyline(
                points=[
                    Point(x_position=500, y_position=120),
                    Point(x_position=550, y_position=115),
                ],
                stroke="#1d70b8",
                stroke_dasharray="",
            )
        ],
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
                value=datetime(2022, 1, 1, 0, 0, tzinfo=timezone.utc),
                label="Jan",
                x_position=100,
                y_position=275,
                label_line_2="2022",
            ),
            ChartAxisTick(
                value=datetime(2022, 2, 1, 0, 0, tzinfo=timezone.utc),
                label="Feb",
                x_position=150,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
                label="Mar",
                x_position=200,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 4, 1, 0, 0, tzinfo=timezone.utc),
                label="Apr",
                x_position=250,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 5, 1, 0, 0, tzinfo=timezone.utc),
                label="May",
                x_position=300,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 6, 1, 0, 0, tzinfo=timezone.utc),
                label="Jun",
                x_position=350,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 7, 1, 0, 0, tzinfo=timezone.utc),
                label="Jul",
                x_position=400,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 8, 1, 0, 0, tzinfo=timezone.utc),
                label="Aug",
                x_position=450,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 9, 1, 0, 0, tzinfo=timezone.utc),
                label="Sep",
                x_position=500,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 10, 1, 0, 0, tzinfo=timezone.utc),
                label="Oct",
                x_position=550,
                y_position=275,
                label_line_2="",
            ),
            ChartAxisTick(
                value=datetime(2022, 11, 1, 0, 0, tzinfo=timezone.utc),
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
        graph_height=250,
        graph_width=600,
        chart_height=330,
        chart_width=680,
        x_axis_tick_y2=260,
        y_axis_tick_x1=-10,
    )


@pytest.mark.parametrize(
    "index, expected_result",
    [
        (0, PolylineStroke(stroke="#1d70b8", dasharray="")),
        (1, PolylineStroke(stroke="#00703c", dasharray="2")),
        (2, PolylineStroke(stroke="#4c2c92", dasharray="6")),
        (3, PolylineStroke(stroke="#d4351c", dasharray="2 2 8 4")),
    ],
)
def test_get_polyline_stroke(index: int, expected_result: PolylineStroke):
    assert get_polyline_stroke(index) == expected_result
