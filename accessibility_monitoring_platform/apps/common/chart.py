""" Utility functions for calculating metrics and charts """

from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
from typing import List, Union

from django.utils import timezone

from .metrics import TimeseriesDatapoint


GRAPH_HEIGHT: int = 250
GRAPH_WIDTH: int = 600
CHART_HEIGHT_EXTRA: int = 50
CHART_WIDTH_EXTRA: int = 150
CHART_HEIGHT: int = GRAPH_HEIGHT + CHART_HEIGHT_EXTRA
CHART_WIDTH: int = GRAPH_WIDTH + CHART_WIDTH_EXTRA
X_AXIS_STEP: int = 50
X_AXIS_TICK_HEIGHT: int = 10
X_AXIS_LABEL_Y_OFFSET: int = 25
DOTTED_LINE_DASHARRAY: str = "5"
LINE_COLOURS: List[str] = [
    "#1d70b8",  # govuk-colour("blue")
    "#f47738",  # govuk-colour("orange")
    "#d53880",  # govuk-colour("pink")
    "#00703c",  # govuk-colour("green")
]


@dataclass
class ChartAxisTick:
    value: Union[int, datetime]
    label: str
    x_position: int
    y_position: int
    label_line_2: str = ""


Y_AXIS_250: List[ChartAxisTick] = [
    ChartAxisTick(value=250, label="250", x_position=0, y_position=0),
    ChartAxisTick(value=200, label="200", x_position=0, y_position=50),
    ChartAxisTick(value=150, label="150", x_position=0, y_position=100),
    ChartAxisTick(value=100, label="100", x_position=0, y_position=150),
    ChartAxisTick(value=50, label="50", x_position=0, y_position=200),
    ChartAxisTick(value=0, label="0", x_position=0, y_position=250),
]
Y_AXIS_100: List[ChartAxisTick] = [
    ChartAxisTick(value=100, label="100", x_position=0, y_position=0),
    ChartAxisTick(value=80, label="80", x_position=0, y_position=50),
    ChartAxisTick(value=60, label="60", x_position=0, y_position=100),
    ChartAxisTick(value=40, label="40", x_position=0, y_position=150),
    ChartAxisTick(value=20, label="20", x_position=0, y_position=200),
    ChartAxisTick(value=0, label="0", x_position=0, y_position=250),
]
Y_AXIS_50: List[ChartAxisTick] = [
    ChartAxisTick(value=50, label="50", x_position=0, y_position=0),
    ChartAxisTick(value=40, label="40", x_position=0, y_position=50),
    ChartAxisTick(value=30, label="30", x_position=0, y_position=100),
    ChartAxisTick(value=20, label="20", x_position=0, y_position=150),
    ChartAxisTick(value=10, label="10", x_position=0, y_position=200),
    ChartAxisTick(value=0, label="0", x_position=0, y_position=250),
]
MULTIPLIER_100_TO_250: float = 250 / 100
MULTIPLIER_50_TO_250: float = 250 / 50


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
class TimeseriesLineChart:
    x_axis: List[ChartAxisTick]
    y_axis: List[ChartAxisTick]
    polylines: List[Polyline]
    graph_height: int = GRAPH_HEIGHT
    graph_width: int = GRAPH_WIDTH
    chart_height: int = CHART_HEIGHT
    chart_width: int = CHART_WIDTH
    x_axis_tick_y2: int = GRAPH_HEIGHT + X_AXIS_TICK_HEIGHT


def calculate_x_position_from_metric_date(now: datetime, metric_date: datetime) -> int:
    """Calculate position of metric on x-axis from current and metric months."""
    row_offset: int = (now.year - metric_date.year) * 12 + now.month - metric_date.month
    return X_AXIS_STEP * abs(12 - row_offset)


def build_position(
    now: datetime, max_value: int, value: int, metric_date: datetime
) -> Point:
    """Work out the position of a point on the line in a timeseries line chart"""
    x_position: int = calculate_x_position_from_metric_date(
        now=now, metric_date=metric_date
    )
    if max_value > 100:
        y_position: int = GRAPH_HEIGHT - value
    elif max_value > 50:
        y_position: int = int(GRAPH_HEIGHT - (value * MULTIPLIER_100_TO_250))
    else:
        y_position: int = int(GRAPH_HEIGHT - (value * MULTIPLIER_50_TO_250))
    return Point(x_position=x_position, y_position=y_position)


def build_13_month_x_axis() -> List[ChartAxisTick]:
    """Build x-axis labels for chart based on the current month"""
    now: datetime = timezone.now()
    current_month: int = now.month
    value_date: datetime = datetime(
        now.year - 1, current_month, 1, tzinfo=datetime_timezone.utc
    )
    x_axis: List[ChartAxisTick] = []
    for x_position in range(0, 650, 50):
        x_axis_tick: ChartAxisTick = ChartAxisTick(
            value=value_date,
            label=value_date.strftime("%b"),
            x_position=x_position,
            y_position=GRAPH_HEIGHT + X_AXIS_LABEL_Y_OFFSET,
        )
        if value_date.month == 1:
            x_axis_tick.label_line_2 = str(value_date.year)
        x_axis.append(x_axis_tick)
        if current_month < 12:
            current_month += 1
        else:
            current_month = 1
        value_date = datetime(
            now.year - 1, current_month, 1, tzinfo=datetime_timezone.utc
        )
    return x_axis


def build_cases_y_axis(max_value: int) -> List[ChartAxisTick]:
    if max_value > 100:
        return Y_AXIS_250
    elif max_value > 50:
        return Y_AXIS_100
    else:
        return Y_AXIS_50


def build_yearly_metric_chart(
    data_sequences: List[List[TimeseriesDatapoint]],
) -> TimeseriesLineChart:
    """
    Given numbers of things done each month, derive the values needed to draw
    a line chart.
    """
    now: datetime = timezone.now()
    max_value: int = max(
        [item.value for data_sequence in data_sequences for item in data_sequence]
    )
    polylines = []
    for index, data_sequence in enumerate(data_sequences):
        line_colour: str = LINE_COLOURS[index % len(LINE_COLOURS)]
        polylines.append(
            Polyline(
                stroke=line_colour,
                points=[
                    build_position(
                        now, max_value, value=row.value, metric_date=row.datetime
                    )
                    for row in data_sequence[:-1]
                ],
            )
        )
        polylines.append(
            Polyline(
                stroke=line_colour,
                stroke_dasharray=DOTTED_LINE_DASHARRAY,
                points=[
                    build_position(
                        now, max_value, value=row.value, metric_date=row.datetime
                    )
                    for row in data_sequence[-2:]
                ],
            )
        )

    return TimeseriesLineChart(
        polylines=polylines,
        x_axis=build_13_month_x_axis(),
        y_axis=build_cases_y_axis(max_value=max_value),
    )


def get_line_stroke(index: int) -> str:
    """Return colour to use when drawing a polyline in a chart"""
    return LINE_COLOURS[index % len(LINE_COLOURS)]
