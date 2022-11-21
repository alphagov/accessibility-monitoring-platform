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
class TimeseriesDatapoint:
    datetime: datetime
    value: int


def calculate_current_month_progress(
    label: str, this_month_value: int, last_month_value: int
) -> Dict[str, Union[str, int]]:
    """
    Given the current day of the month compare a number of things done
    to date in the current month to the total done in the previous month
    and express as a percentage above or below.
    """
    now: datetime = timezone.now()
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
        for fieldname, good_value in ACCESSIBILITY_STATEMENT_TESTS.items():
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


def build_html_table_rows(
    first_series: List[TimeseriesDatapoint],
    second_series: List[TimeseriesDatapoint],
) -> List[Dict[str, Union[datetime, int]]]:
    """
    Given two lists of timeseries data, merge them into a single list of data
    for a 3-column html table
    """
    html_table_data: Dict[datetime, Dict[str, Union[datetime, int]]] = {
        timeseries_datapoint.datetime: {
            "datetime": timeseries_datapoint.datetime,
            "first_value": timeseries_datapoint.value,
        }
        for timeseries_datapoint in first_series
    }
    for timeseries_datapoint in second_series:
        if timeseries_datapoint.datetime in html_table_data:
            html_table_data[timeseries_datapoint.datetime][
                "second_value"
            ] = timeseries_datapoint.value
        else:
            html_table_data[timeseries_datapoint.datetime] = {
                "datetime": timeseries_datapoint.datetime,
                "second_value": timeseries_datapoint.value,
            }
    return sorted(list(html_table_data.values()), key=lambda x: x["datetime"])
