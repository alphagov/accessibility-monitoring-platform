""" Utility functions for calculating metrics and charts """

import calendar
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
)

from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models.query import QuerySet

from ..audits.models import Audit

ACCESSIBILITY_STATEMENT_FIELD_VALID_VALUE: Dict[str, str] = {
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
class TimeseriesDatapoint:
    datetime: datetime
    value: int


@dataclass
class Timeseries:
    datapoints: List[TimeseriesDatapoint]
    label: str = ""


@dataclass
class TimeseriesHtmlTable:
    column_names: List[str]
    rows: List[List[str]]


def calculate_current_month_progress(
    now: datetime, label: str, this_month_value: int, last_month_value: int
) -> Dict[str, Union[str, int]]:
    """
    Given the current day of the month compare a number of things done
    to date in the current month to the total done in the previous month
    and express that as a percentage above or below.
    """
    _, days_in_current_month = calendar.monthrange(now.year, now.month)
    metric: Dict[str, Union[str, int]] = {
        "label": label,
        "this_month_value": this_month_value,
        "last_month_value": last_month_value,
    }
    if last_month_value == 0:
        return metric

    percentage_progress: int = int(
        ((this_month_value / (now.day / days_in_current_month)) / last_month_value)
        * 100
    )
    expected_progress_difference: int = percentage_progress - 100
    expected_progress_difference_label: str = (
        "under" if expected_progress_difference < 0 else "over"
    )
    metric["expected_progress_difference"] = abs(expected_progress_difference)
    metric["expected_progress_difference_label"] = expected_progress_difference_label

    return metric


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
        for fieldname, good_value in ACCESSIBILITY_STATEMENT_FIELD_VALID_VALUE.items():
            if getattr(audit, fieldname) != good_value:
                statement_issues_count += 1
                if getattr(audit, f"audit_retest_{fieldname}") == good_value:
                    fixed_statement_issues_count += 1
    return (fixed_statement_issues_count, statement_issues_count)


def group_timeseries_data_by_month(
    queryset: QuerySet, date_column_name: str, start_date: datetime
) -> List[TimeseriesDatapoint]:
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
        TimeseriesDatapoint(
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


def build_html_table(
    table_data: List[Timeseries],
) -> TimeseriesHtmlTable:
    """
    Given lists of timeseries data, merge them into a context object for a
    single HTML table
    """
    column_names: List[str] = ["Month"] + [
        timeseries.label for timeseries in table_data
    ]
    empty_row: List[str] = ["" for _ in range(len(table_data))]
    html_table_data: Dict[datetime, List[str]] = {}
    for timeseries in table_data:
        for datapoint in timeseries.datapoints:
            html_table_data[datapoint.datetime] = [
                datapoint.datetime.strftime("%B %Y")
            ] + empty_row
    for index, timeseries in enumerate(table_data, start=1):
        for datapoint in timeseries.datapoints:
            html_table_data[datapoint.datetime][index] = intcomma(datapoint.value)

    return TimeseriesHtmlTable(
        column_names=column_names,
        rows=list(OrderedDict(sorted(html_table_data.items())).values()),
    )
