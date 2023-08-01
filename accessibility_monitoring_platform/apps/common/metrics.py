""" Utility functions for calculating metrics and charts """

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
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
FIRST_COLUMN_HEADER: str = "Month"


@dataclass
class ThirtyDayMetric:
    label: str
    last_30_day_count: int
    previous_30_day_count: int

    @property
    def progress_label(self) -> str:
        if self.last_30_day_count < self.previous_30_day_count:
            return "under"
        return "over"

    @property
    def progress_percentage(self) -> Optional[int]:
        if self.previous_30_day_count > 0:
            return abs(
                100 - int((self.last_30_day_count * 100) / self.previous_30_day_count)
            )
        return None


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
    current_year: int = start_date.year
    current_month: int = start_date.month
    month_dates: List[datetime] = []
    for _ in range(13):
        month_dates.append(
            datetime(current_year, current_month, 1, tzinfo=timezone.utc)
        )
        if current_month < 12:
            current_month += 1
        else:
            current_month = 1
            current_year += 1
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
    columns: List[Timeseries],
) -> TimeseriesHtmlTable:
    """
    Given lists of timeseries data, merge them into a context object for a
    single HTML table
    """
    column_names: List[str] = [FIRST_COLUMN_HEADER] + [
        timeseries.label for timeseries in columns
    ]
    empty_row: List[str] = ["" for _ in range(len(columns))]
    html_columns: Dict[datetime, List[str]] = {}
    for timeseries in columns:
        for datapoint in timeseries.datapoints:
            html_columns[datapoint.datetime] = [
                datapoint.datetime.strftime("%B %Y")
            ] + empty_row
    for index, timeseries in enumerate(columns, start=1):
        for datapoint in timeseries.datapoints:
            html_columns[datapoint.datetime][index] = intcomma(datapoint.value)

    return TimeseriesHtmlTable(
        column_names=column_names,
        rows=list(OrderedDict(sorted(html_columns.items())).values()),
    )


def convert_timeseries_pair_to_ratio(
    label: str, partial_timeseries: Timeseries, total_timeseries: Timeseries
) -> Timeseries:
    """
    Given partial and total timeseries return a timeseries where the values
    are the first divided by the second as a percentage
    """
    datapoints: List[TimeseriesDatapoint] = []
    for partial, total in zip(
        partial_timeseries.datapoints, total_timeseries.datapoints
    ):
        if total.value == 0:
            value: int = 0
        else:
            value: int = int((partial.value * 100) / total.value)
        datapoints.append(TimeseriesDatapoint(datetime=total.datetime, value=value))
    return Timeseries(label=label, datapoints=datapoints)


def convert_timeseries_to_cumulative(timeseries: Timeseries) -> Timeseries:
    """
    Given partial and total timeseries return a timeseries where the values
    are the first divided by the second as a percentage
    """
    cumulative_value: int = 0
    cumulative_datapoints: List[TimeseriesDatapoint] = []
    for datapoint in timeseries.datapoints:
        cumulative_value += datapoint.value
        cumulative_datapoints.append(
            TimeseriesDatapoint(datetime=datapoint.datetime, value=cumulative_value)
        )
    timeseries.datapoints = cumulative_datapoints
    return timeseries
