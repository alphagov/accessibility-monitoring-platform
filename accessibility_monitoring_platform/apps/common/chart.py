""" Utility functions for calculating metrics and charts """

from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
from typing import List, Union

from django.utils import timezone

from .metrics import Timeseries, TimeseriesDatapoint

GRAPH_HEIGHT: int = 250
GRAPH_WIDTH: int = 600
CHART_HEIGHT_EXTRA: int = 50
CHART_WIDTH_EXTRA: int = 150
CHART_HEIGHT: int = GRAPH_HEIGHT + CHART_HEIGHT_EXTRA
CHART_WIDTH: int = GRAPH_WIDTH + CHART_WIDTH_EXTRA
AXIS_TICK_LENGTH: int = 10
X_AXIS_STEP: int = 50
X_AXIS_LABEL_Y_OFFSET: int = 25
STROKE_DASHARRAY_DOTTED: str = "5"
STROKE_COLOURS: List[str] = [
    "#1d70b8",  # govuk-colour("blue")
    "#f47738",  # govuk-colour("orange")
    "#d53880",  # govuk-colour("pink")
    "#00703c",  # govuk-colour("green")
]
LINE_LABEL_X_STEP: int = 110
LINE_LABEL_Y: int = -10
LINE_LABEL_STROKE_Y: int = -15
LINE_LABEL_STROKE_LENGTH: int = 20
LINE_LABEL_X_OFFSET: int = LINE_LABEL_STROKE_LENGTH + 10


@dataclass
class ChartAxisTick:
    value: Union[int, datetime]
    label: str
    x_position: int = 0
    y_position: int = 0
    label_line_2: str = ""


Y_AXIS_50: List[ChartAxisTick] = [
    ChartAxisTick(value=50, label="50", y_position=0),
    ChartAxisTick(value=40, label="40", y_position=50),
    ChartAxisTick(value=30, label="30", y_position=100),
    ChartAxisTick(value=20, label="20", y_position=150),
    ChartAxisTick(value=10, label="10", y_position=200),
    ChartAxisTick(value=0, label="0", y_position=250),
]
Y_AXIS_100: List[ChartAxisTick] = [
    ChartAxisTick(value=100, label="100", y_position=0),
    ChartAxisTick(value=80, label="80", y_position=50),
    ChartAxisTick(value=60, label="60", y_position=100),
    ChartAxisTick(value=40, label="40", y_position=150),
    ChartAxisTick(value=20, label="20", y_position=200),
    ChartAxisTick(value=0, label="0", y_position=250),
]
Y_AXIS_250: List[ChartAxisTick] = [
    ChartAxisTick(value=250, label="250", y_position=0),
    ChartAxisTick(value=200, label="200", y_position=50),
    ChartAxisTick(value=150, label="150", y_position=100),
    ChartAxisTick(value=100, label="100", y_position=150),
    ChartAxisTick(value=50, label="50", y_position=200),
    ChartAxisTick(value=0, label="0", y_position=250),
]
MULTIPLIER_50_TO_250: float = 250 / 50
MULTIPLIER_100_TO_250: float = 250 / 100


@dataclass
class Point:
    x_position: int
    y_position: int


@dataclass
class Polyline:
    points: List[Point]
    stroke: str
    stroke_dasharray: str = ""


@dataclass
class LineLabel:
    """Individual line and label in chart key"""

    label: str
    line_stroke: str
    label_x: int
    label_y: int
    line_x1: int
    line_x2: int
    line_y: int


@dataclass
class LineChart:
    """Context for SVG line of chart"""

    key: List[LineLabel]
    polylines: List[Polyline]
    x_axis: List[ChartAxisTick]
    y_axis: List[ChartAxisTick]
    graph_height: int = GRAPH_HEIGHT
    graph_width: int = GRAPH_WIDTH
    chart_height: int = CHART_HEIGHT
    chart_width: int = CHART_WIDTH
    x_axis_tick_y2: int = GRAPH_HEIGHT + AXIS_TICK_LENGTH
    y_axis_tick_x1: int = AXIS_TICK_LENGTH * -1


def calculate_x_position_from_datapoint_datetime(
    now: datetime, datapoint_datetime: datetime
) -> int:
    """
    Calculate position of timeseries datapoint on x-axis from current and
    datapoint months.
    """
    row_offset: int = (
        (now.year - datapoint_datetime.year) * 12 + now.month - datapoint_datetime.month
    )
    return X_AXIS_STEP * abs(12 - row_offset)


def calculate_timeseries_point(
    now: datetime, max_value: int, datapoint: TimeseriesDatapoint
) -> Point:
    """Work out the position of a point on the line in a timeseries line chart"""
    x_position: int = calculate_x_position_from_datapoint_datetime(
        now=now, datapoint_datetime=datapoint.datetime
    )
    if max_value > 100:
        y_position: int = GRAPH_HEIGHT - datapoint.value
    elif max_value > 50:
        y_position: int = int(GRAPH_HEIGHT - (datapoint.value * MULTIPLIER_100_TO_250))
    else:
        y_position: int = int(GRAPH_HEIGHT - (datapoint.value * MULTIPLIER_50_TO_250))
    return Point(x_position=x_position, y_position=y_position)


def build_13_month_x_axis() -> List[ChartAxisTick]:
    """Build monthly x-axis for timeseries chart ending on the current month"""
    now: datetime = timezone.now()
    current_month: int = now.month
    current_year: int = now.year - 1
    tick_datetime: datetime = datetime(
        current_year, current_month, 1, tzinfo=datetime_timezone.utc
    )
    x_axis: List[ChartAxisTick] = []
    for x_position in range(0, 650, 50):
        x_axis_tick: ChartAxisTick = ChartAxisTick(
            value=tick_datetime,
            label=tick_datetime.strftime("%b"),
            x_position=x_position,
            y_position=GRAPH_HEIGHT + X_AXIS_LABEL_Y_OFFSET,
        )
        if tick_datetime.month == 1:
            x_axis_tick.label_line_2 = str(tick_datetime.year)
        x_axis.append(x_axis_tick)
        if current_month < 12:
            current_month += 1
        else:
            current_month = 1
            current_year += 1
        tick_datetime = datetime(
            current_year, current_month, 1, tzinfo=datetime_timezone.utc
        )
    return x_axis


def get_y_axis(max_value: int) -> List[ChartAxisTick]:
    """Return y-axis based on the maximum value in the polyline"""
    if max_value > 100:
        return Y_AXIS_250
    elif max_value > 50:
        return Y_AXIS_100
    else:
        return Y_AXIS_50


def build_yearly_metric_chart(
    lines: List[Timeseries],
) -> LineChart:
    """
    Given timeseries datapoints, derive the values needed to draw
    a line chart.
    """
    now: datetime = timezone.now()
    values: List[int] = []
    for timeseries in lines:
        for datapoint in timeseries.datapoints:
            values.append(datapoint.value)
    max_value: int = max(values) if values else 0
    polylines = []
    chart_key: List[LineLabel] = []
    for index, timeseries in enumerate(lines):
        stroke: str = STROKE_COLOURS[index % len(STROKE_COLOURS)]
        if timeseries.label:
            chart_key.append(
                LineLabel(
                    label=timeseries.label,
                    line_stroke=stroke,
                    label_x=(LINE_LABEL_X_STEP * index) + LINE_LABEL_X_OFFSET,
                    label_y=LINE_LABEL_Y,
                    line_x1=LINE_LABEL_X_STEP * index,
                    line_x2=(LINE_LABEL_X_STEP * index) + LINE_LABEL_STROKE_LENGTH,
                    line_y=LINE_LABEL_STROKE_Y,
                )
            )
        if (
            timeseries.datapoints
            and timeseries.datapoints[-1].datetime.month == now.month
        ):
            penultimate_datapoints: List[TimeseriesDatapoint] = timeseries.datapoints[
                :-1
            ]
            last_month_datapoints: List[TimeseriesDatapoint] = timeseries.datapoints[
                -2:
            ]
        else:
            penultimate_datapoints: List[TimeseriesDatapoint] = timeseries.datapoints
            last_month_datapoints: List[TimeseriesDatapoint] = []
        polylines.append(
            Polyline(
                stroke=stroke,
                points=[
                    calculate_timeseries_point(now, max_value, datapoint=datapoint)
                    for datapoint in penultimate_datapoints
                ],
            )
        )
        polylines.append(
            Polyline(
                stroke=stroke,
                stroke_dasharray=STROKE_DASHARRAY_DOTTED,
                points=[
                    calculate_timeseries_point(now, max_value, datapoint=datapoint)
                    for datapoint in last_month_datapoints
                ],
            )
        )

    return LineChart(
        polylines=polylines,
        key=chart_key,
        x_axis=build_13_month_x_axis(),
        y_axis=get_y_axis(max_value=max_value),
    )


def get_line_stroke(index: int) -> str:
    """Return colour to use when drawing a polyline in a chart"""
    return STROKE_COLOURS[index % len(STROKE_COLOURS)]
