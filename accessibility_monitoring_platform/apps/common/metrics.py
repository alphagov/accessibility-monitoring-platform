""" Utility functions for calculating metrics and charts """

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone as datetime_timezone
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
)

from django.db.models.query import QuerySet
from django.utils import timezone

from ..audits.models import Audit

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
ACCESSIBILITY_STATEMENT_TESTS: Dict[str, str] = {
    "declaration_state": "present",
    "scope_state": "present",
    "compliance_state": "present",
    "non_regulation_state": "present",
    "preparation_date_state": "present",
    "method_state": "present",
    "review_state": "present",
    "feedback_state": "present",
    "contact_information_state": "present",
    "enforcement_procedure_state": "present",
    "access_requirements_state": "req-met",
}


@dataclass
class TimeseriesData:
    datetime: datetime
    value: int


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


def calculate_current_month_progress(
    label: str, number_done_this_month: int, number_done_last_month: int
) -> Dict[str, Union[str, int]]:
    """
    Given the current day of the month compare a number of things done
    to date in the current month to the total done in the previous month
    and express as a percentage above or below.
    """
    now: datetime = timezone.now()
    days_in_current_month: int = calendar.monthrange(now.year, now.month)[1]
    metric: Dict[str, Union[str, int]] = {
        "label": label,
        "number_done_this_month": number_done_this_month,
        "number_done_last_month": number_done_last_month,
    }
    if number_done_last_month == 0:
        return metric

    percentage_progress: int = int(
        (
            (number_done_this_month / (now.day / days_in_current_month))
            / number_done_last_month
        )
        * 100
    )
    expected_progress_difference: int = percentage_progress - 100
    expected_progress_difference_label: str = (
        "under" if expected_progress_difference < 0 else "over"
    )
    metric["expected_progress_difference"] = abs(expected_progress_difference)
    metric["expected_progress_difference_label"] = expected_progress_difference_label
    return metric


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
    data_sequences: List[List[TimeseriesData]],
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


def calculate_metric_progress(
    label: str, partial_count: int, total_count: int
) -> Dict[str, Any]:
    """Given a number done and a total return a percentage metric"""
    percentage: int = int(100 * partial_count / total_count) if total_count > 0 else 0
    return {
        "label": label,
        "partial_count": partial_count,
        "total_count": total_count,
        "percentage": percentage,
    }


def count_statement_issues(audits: QuerySet[Audit]) -> Tuple[int, int]:
    """Count numbers of statement errors and how many were fixed"""
    statement_issues_count: int = 0
    fixed_statement_issues_count: int = 0
    for audit in audits:
        for fieldname, good_value in ACCESSIBILITY_STATEMENT_TESTS.items():
            statement_issues_count += 1
            if getattr(audit, fieldname) != good_value:
                if getattr(audit, f"audit_retest_{fieldname}") == good_value:
                    fixed_statement_issues_count += 1
    return (fixed_statement_issues_count, statement_issues_count)


def build_timeseries_data(
    queryset: QuerySet, date_column_name: str, start_date: datetime
) -> List[TimeseriesData]:
    """
    Given a queryset containing a timestamp field return the numbers found
    in each month.
    """
    items_since_start_date: QuerySet = queryset.filter(
        **{f"{date_column_name}__gte": start_date}
    )
    month_dates: QuerySet = items_since_start_date.dates(  # type: ignore
        date_column_name, kind="month"
    )
    return [
        TimeseriesData(
            datetime=month_date,
            value=items_since_start_date.filter(
                **{
                    f"{date_column_name}__year": month_date.year,
                    f"{date_column_name}__month": month_date.month,
                }
            ).count(),
        )
        for month_date in month_dates
    ]


def build_html_table_rows(
    first_series: List[TimeseriesData],
    second_series: List[TimeseriesData],
) -> List[Dict[str, Union[datetime, int]]]:
    """
    Given two lists of timeseries data, merge them into a single list of data
    for a 3-column html table
    """
    first_position: int = 0
    second_position: int = 0
    html_table_rows: List[Dict[str, Union[datetime, int]]] = []
    while first_position < len(first_series) and second_position < len(second_series):
        if (
            first_series[first_position].datetime
            < second_series[second_position].datetime
        ):
            html_table_rows.append(
                {
                    "datetime": first_series[first_position].datetime,
                    "first_value": first_series[first_position].value,
                }
            )
            first_position += 1
        elif (
            second_series[second_position].datetime
            < first_series[first_position].datetime
        ):
            html_table_rows.append(
                {
                    "datetime": second_series[second_position].datetime,
                    "second_value": second_series[second_position].value,
                }
            )
            second_position += 1
        else:
            html_table_rows.append(
                {
                    "datetime": first_series[first_position].datetime,
                    "first_value": first_series[first_position].value,
                    "second_value": second_series[second_position].value,
                }
            )
            first_position += 1
            second_position += 1
    while first_position < len(first_series):
        html_table_rows.append(
            {
                "datetime": first_series[first_position].datetime,
                "first_value": first_series[first_position].value,
            }
        )
        first_position += 1
    while second_position < len(second_series):
        html_table_rows.append(
            {
                "datetime": second_series[second_position].datetime,
                "second_value": second_series[second_position].value,
            }
        )
        second_position += 1
    return html_table_rows
