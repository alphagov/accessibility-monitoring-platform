""" Utility functions for calculating metrics and charts """
from datetime import datetime

import calendar
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from django.utils import timezone

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
Y_AXIS_LABELS_250: List[Dict[str, Union[str, int]]] = [
    {"label": "250", "y": 0},
    {"label": "200", "y": 50},
    {"label": "150", "y": 100},
    {"label": "100", "y": 150},
    {"label": "50", "y": 200},
    {"label": "0", "y": 250},
]
Y_AXIS_LABELS_100: List[Dict[str, Union[str, int]]] = [
    {"label": "100", "y": 0},
    {"label": "80", "y": 50},
    {"label": "60", "y": 100},
    {"label": "40", "y": 150},
    {"label": "20", "y": 200},
    {"label": "0", "y": 250},
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
        List[Dict[str, Union[str, int]]],
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
        "y_axis_labels": build_cases_y_axis_labels(max_value=max_value),
    }


def build_x_axis_labels() -> List[Dict[str, Union[str, int]]]:
    """Build x-axis labels for chart based on the current month"""
    now: datetime = timezone.now()
    current_month: int = now.month
    x_axis_labels: List[Dict[str, Union[str, int]]] = []
    for count, x_position in enumerate(range(0, 650, 50)):
        x_axis_label: Dict[str, Union[str, int]] = {
            "label": X_AXIS_LABELS[(count + current_month - 1) % 12],
            "x": x_position,
        }
        if x_axis_label["label"] == "Jan":
            x_axis_label["label_line_2"] = now.year
        x_axis_labels.append(x_axis_label)
    if current_month == 1:
        x_axis_labels[0]["label_line_2"] = now.year - 1
    return x_axis_labels


def build_cases_y_axis_labels(max_value: int) -> List[Dict[str, Union[str, int]]]:
    return Y_AXIS_LABELS_250 if max_value > 100 else Y_AXIS_LABELS_100


def calculate_x_axis_position_from_month(now: datetime, metric_date: datetime) -> int:
    """Calculate position of metric on x-axis from current and metric months."""
    row_offset: int = (now.year - metric_date.year) * 12 + now.month - metric_date.month
    return X_AXIS_STEP * abs(12 - row_offset)


def calculate_current_year_progress(
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
