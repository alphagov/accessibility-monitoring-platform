""" Utility functions for calculating metrics and charts """

from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
import math
from typing import List, Union

from django.utils import timezone

from .metrics import Timeseries, TimeseriesDatapoint

GRAPH_HEIGHT: int = 250
GRAPH_WIDTH: int = 600
CHART_HEIGHT_EXTRA: int = 80
CHART_WIDTH_EXTRA: int = 80
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
Y_AXIS_NUMBER_OF_TICKS: int = 5


@dataclass
class ChartAxisTick:
    value: Union[int, datetime]
    label: str
    x_position: int = 0
    y_position: int = 0
    label_line_2: str = ""


Y_AXIS_RATIO: List[ChartAxisTick] = [
    ChartAxisTick(value=100, label="1.0", y_position=0),
    ChartAxisTick(value=80, label="0.8", y_position=50),
    ChartAxisTick(value=60, label="0.6", y_position=100),
    ChartAxisTick(value=40, label="0.4", y_position=150),
    ChartAxisTick(value=20, label="0.2", y_position=200),
    ChartAxisTick(value=0, label="0.0", y_position=250),
]


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
    now: datetime, y_tick_size: int, datapoint: TimeseriesDatapoint
) -> Point:
    """Work out the position of a point on the line in a timeseries line chart"""
    x_position: int = calculate_x_position_from_datapoint_datetime(
        now=now, datapoint_datetime=datapoint.datetime
    )
    y_position: int = int(
        GRAPH_HEIGHT - (datapoint.value * 250 / (y_tick_size * Y_AXIS_NUMBER_OF_TICKS))
    )
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


def build_y_axis(y_tick_size: int, is_ratio: bool = False) -> List[ChartAxisTick]:
    """Return y-axis based on the maximum value in the polyline"""
    if is_ratio:
        return Y_AXIS_RATIO
    return [
        ChartAxisTick(value=y_tick_size * 5, label=str(y_tick_size * 5), y_position=0),
        ChartAxisTick(value=y_tick_size * 4, label=str(y_tick_size * 4), y_position=50),
        ChartAxisTick(
            value=y_tick_size * 3, label=str(y_tick_size * 3), y_position=100
        ),
        ChartAxisTick(
            value=y_tick_size * 2, label=str(y_tick_size * 2), y_position=150
        ),
        ChartAxisTick(value=y_tick_size, label=str(y_tick_size), y_position=200),
        ChartAxisTick(value=0, label="0", y_position=250),
    ]


def calculate_y_tick_size(max_value: int) -> int:
    """
    For a maximum value calculate the next highest nice maximum y-axis tick
    value
    """
    if max_value <= 10:
        max_tick: int = 5 if max_value <= 5 else 10
        tick = int(max_tick / 5)
    else:
        scale = int(math.log10(max_value))
        multiplier: int = 10**scale
        for step in [1, 2, 5, 10]:
            max_tick: int = step * multiplier
            if max_tick >= max_value:
                break
        tick = int(max_tick / 5)  # type: ignore
    return tick


def build_yearly_metric_chart(
    lines: List[Timeseries],
    y_axis_ratio: bool = False,
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
    y_tick_size: int = calculate_y_tick_size(max_value)
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
                    calculate_timeseries_point(now=now, y_tick_size=y_tick_size, datapoint=datapoint)
                    for datapoint in penultimate_datapoints
                ],
            )
        )
        polylines.append(
            Polyline(
                stroke=stroke,
                stroke_dasharray=STROKE_DASHARRAY_DOTTED,
                points=[
                    calculate_timeseries_point(now=now, y_tick_size=y_tick_size, datapoint=datapoint)
                    for datapoint in last_month_datapoints
                ],
            )
        )

    return LineChart(
        polylines=polylines,
        key=chart_key,
        x_axis=build_13_month_x_axis(),
        y_axis=build_y_axis(y_tick_size=y_tick_size, is_ratio=y_axis_ratio),
    )


def get_line_stroke(index: int) -> str:
    """Return colour to use when drawing a polyline in a chart"""
    return STROKE_COLOURS[index % len(STROKE_COLOURS)]
