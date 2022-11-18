""" Utility functions for calculating metrics and charts """

import calendar
from dataclasses import dataclass
from datetime import datetime
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
X_AXIS_LABELS: List[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
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
MULTIPLIER_100_TO_250: float = 250 / 100


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


def build_yearly_metric_chart(
    label: str, all_table_rows: List[Dict[str, Union[datetime, int]]]
) -> Dict[
    str,
    Union[
        str,
        int,
        List[Dict[str, Union[datetime, int]]],
        List[ChartAxisTick],
    ],
]:
    """
    Given numbers of things done each month, derive the values needed to draw
    a line chart.
    """
    now: datetime = timezone.now()
    max_value: int = max([table_row["count"] for table_row in all_table_rows])  # type: ignore
    for table_row in all_table_rows:
        if max_value > 100:
            table_row["y"] = GRAPH_HEIGHT - table_row["count"]  # type: ignore
        else:
            table_row["y"] = GRAPH_HEIGHT - (table_row["count"] * MULTIPLIER_100_TO_250)  # type: ignore
        table_row["x"] = calculate_x_axis_position_from_month(
            now=now, metric_date=table_row["month_date"]  # type: ignore
        )
    return {
        "label": label,
        "all_table_rows": all_table_rows,
        "previous_month_rows": all_table_rows[:-1],
        "current_month_rows": all_table_rows[-2:],
        "graph_height": GRAPH_HEIGHT,
        "graph_width": GRAPH_WIDTH,
        "chart_height": CHART_HEIGHT,
        "chart_width": CHART_WIDTH,
        "x_axis_tick_y2": GRAPH_HEIGHT + X_AXIS_TICK_HEIGHT,
        "x_axis_label_y": GRAPH_HEIGHT + X_AXIS_LABEL_Y_OFFSET,
        "y_axis": build_cases_y_axis(max_value=max_value),
    }


def build_13_month_x_axis() -> List[ChartAxisTick]:
    """Build x-axis labels for chart based on the current month"""
    now: datetime = timezone.now()
    current_month: int = now.month
    value_date: datetime = datetime(now.year - 1, current_month, 1, tzinfo=timezone.utc)
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
        value_date = datetime(now.year - 1, current_month, 1, tzinfo=timezone.utc)
    return x_axis


def build_cases_y_axis(max_value: int) -> List[ChartAxisTick]:
    return Y_AXIS_250 if max_value > 100 else Y_AXIS_100


def calculate_x_axis_position_from_month(now: datetime, metric_date: datetime) -> int:
    """Calculate position of metric on x-axis from current and metric months."""
    row_offset: int = (now.year - metric_date.year) * 12 + now.month - metric_date.month
    return X_AXIS_STEP * abs(12 - row_offset)


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
