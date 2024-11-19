""" Utility functions for calculating metrics and charts """

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone

from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models.query import QuerySet
from django.utils import timezone

from ..audits.models import Audit, CheckResult
from ..cases.models import Case, CaseCompliance, CaseStatus
from ..reports.models import ReportVisitsMetrics
from ..s3_read_write.models import S3Report
from .chart import LineChart, Timeseries, TimeseriesDatapoint, build_yearly_metric_chart
from .utils import get_days_ago_timestamp, get_first_of_this_month_last_year

ARCHIVE_ACCESSIBILITY_STATEMENT_FIELD_VALID_VALUE: dict[str, str] = {
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
    def progress_percentage(self) -> int | None:
        if self.previous_30_day_count > 0:
            percentage: int = int(
                (self.last_30_day_count * 100) / self.previous_30_day_count
            )
            if percentage >= 100:
                return percentage - 100
            return 100 - percentage
        return None


@dataclass
class TimeseriesHtmlTable:
    column_names: list[str]
    rows: list[list[str]]


@dataclass
class ProgressMetric:
    label: str
    partial_count: int
    total_count: int

    @property
    def percentage(self) -> int:
        """Given a number done and a total return a percentage metric"""
        return (
            int(100 * self.partial_count / self.total_count)
            if self.total_count > 0
            else 0
        )


@dataclass
class YearlyMetric:
    label: str
    html_table: TimeseriesHtmlTable
    chart: LineChart


@dataclass
class TotalMetric:
    label: str
    total: int


@dataclass
class EqualityBodyCasesMetric:
    label: str
    completed_count: int
    in_progress_count: int


def count_statement_issues(audits: QuerySet[Audit]) -> tuple[int, int]:
    """Count numbers of statement errors and how many were fixed"""
    statement_issues_count: int = 0
    fixed_statement_issues_count: int = 0
    for audit in audits:
        if audit.uses_statement_checks:
            statement_issues_count += audit.failed_statement_check_results.count()
            fixed_statement_issues_count += audit.fixed_statement_check_results.count()
        else:
            for (
                fieldname,
                good_value,
            ) in ARCHIVE_ACCESSIBILITY_STATEMENT_FIELD_VALID_VALUE.items():
                if getattr(audit, f"archive_{fieldname}") != good_value:
                    statement_issues_count += 1
                    if (
                        getattr(audit, f"archive_audit_retest_{fieldname}")
                        == good_value
                    ):
                        fixed_statement_issues_count += 1
    return (fixed_statement_issues_count, statement_issues_count)


def group_timeseries_data_by_month(
    queryset: QuerySet, date_column_name: str, start_date: datetime
) -> list[TimeseriesDatapoint]:
    """
    Given a queryset containing a timestamp field return the numbers found
    in each month.
    """
    items_since_start_date: QuerySet = queryset.filter(
        **{f"{date_column_name}__gte": start_date}
    )
    current_year: int = start_date.year
    current_month: int = start_date.month
    month_dates: list[datetime] = []
    for _ in range(13):
        month_dates.append(
            datetime(current_year, current_month, 1, tzinfo=datetime_timezone.utc)
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
    columns: list[Timeseries],
) -> TimeseriesHtmlTable:
    """
    Merge lists of timeseries data into a context object
    to populate a single HTML table.
    """
    column_names: list[str] = [FIRST_COLUMN_HEADER] + [
        timeseries.label for timeseries in columns
    ]
    number_of_columns: int = len(columns)

    totals_row_label: str = "Totals" if number_of_columns > 1 else "Total"
    totals_row: list[str | int] = [totals_row_label] + [
        0 for _ in range(number_of_columns)
    ]

    html_columns: dict[datetime, list[str]] = {}
    empty_row: list[str] = ["" for _ in range(number_of_columns)]
    for timeseries in columns:
        for datapoint in timeseries.datapoints:
            html_columns[datapoint.datetime] = [
                datapoint.datetime.strftime("%B %Y")
            ] + empty_row
    for index, timeseries in enumerate(columns, start=1):
        for datapoint in timeseries.datapoints:
            html_columns[datapoint.datetime][index] = intcomma(datapoint.value)
            totals_row[index] += datapoint.value

    for index in range(1, len(totals_row)):
        totals_row[index] = intcomma(totals_row[index])

    return TimeseriesHtmlTable(
        column_names=column_names,
        rows=list(OrderedDict(sorted(html_columns.items())).values()) + [totals_row],
    )


def convert_timeseries_pair_to_ratio(
    label: str, partial_timeseries: Timeseries, total_timeseries: Timeseries
) -> Timeseries:
    """
    Given partial and total timeseries return a timeseries where the values
    are the first divided by the second as a percentage
    """
    datapoints: list[TimeseriesDatapoint] = []
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
    cumulative_datapoints: list[TimeseriesDatapoint] = []
    for datapoint in timeseries.datapoints:
        cumulative_value += datapoint.value
        cumulative_datapoints.append(
            TimeseriesDatapoint(datetime=datapoint.datetime, value=cumulative_value)
        )
    timeseries.datapoints = cumulative_datapoints
    return timeseries


def get_case_progress_metrics() -> list[ThirtyDayMetric]:
    """Return case progress metrics"""
    thirty_days_ago: datetime = get_days_ago_timestamp(days=30)
    sixty_days_ago: datetime = get_days_ago_timestamp(days=60)
    return [
        ThirtyDayMetric(
            label="Cases created",
            last_30_day_count=Case.objects.filter(created__gte=thirty_days_ago).count(),
            previous_30_day_count=Case.objects.filter(created__gte=sixty_days_ago)
            .filter(created__lt=thirty_days_ago)
            .count(),
        ),
        ThirtyDayMetric(
            label="Tests completed",
            last_30_day_count=Case.objects.filter(
                testing_details_complete_date__gte=thirty_days_ago
            ).count(),
            previous_30_day_count=Case.objects.filter(
                testing_details_complete_date__gte=sixty_days_ago
            )
            .filter(testing_details_complete_date__lt=thirty_days_ago)
            .count(),
        ),
        ThirtyDayMetric(
            label="Reports sent",
            last_30_day_count=Case.objects.filter(
                report_sent_date__gte=thirty_days_ago
            ).count(),
            previous_30_day_count=Case.objects.filter(
                report_sent_date__gte=sixty_days_ago
            )
            .filter(report_sent_date__lt=thirty_days_ago)
            .count(),
        ),
        ThirtyDayMetric(
            label="Cases closed",
            last_30_day_count=Case.objects.filter(
                completed_date__gte=thirty_days_ago
            ).count(),
            previous_30_day_count=Case.objects.filter(
                completed_date__gte=sixty_days_ago
            )
            .filter(completed_date__lt=thirty_days_ago)
            .count(),
        ),
    ]


def get_case_yearly_metrics() -> list[YearlyMetric]:
    """Return case yearly metrics"""
    yearly_metrics: list[YearlyMetric] = []
    start_date: datetime = get_first_of_this_month_last_year()
    for label, date_column_name in [
        ("Cases created", "created"),
        ("Tests completed", "testing_details_complete_date"),
        ("Reports sent", "report_sent_date"),
        ("Cases completed", "completed_date"),
    ]:
        timeseries: Timeseries = Timeseries(
            label=label,
            datapoints=group_timeseries_data_by_month(
                queryset=Case.objects,
                date_column_name=date_column_name,
                start_date=start_date,
            ),
        )
        yearly_metrics.append(
            YearlyMetric(
                label=f"{label} over the last year",
                html_table=build_html_table(columns=[timeseries]),
                chart=build_yearly_metric_chart(lines=[timeseries]),
            )
        )
    return yearly_metrics


def get_policy_total_metrics() -> list[TotalMetric]:
    """Return policy total metrics"""
    return [
        TotalMetric(
            label="Total reports sent",
            total=Case.objects.exclude(report_sent_date=None).count(),
        ),
        TotalMetric(
            label="Total cases closed",
            total=Case.objects.filter(
                status__status__in=CaseStatus.CLOSED_CASE_STATUSES
            ).count(),
        ),
        TotalMetric(
            label="Total number of accessibility issues found",
            total=CheckResult.objects.filter(
                check_result_state=CheckResult.Result.ERROR
            ).count(),
        ),
        TotalMetric(
            label="Total number of accessibility issues fixed",
            total=CheckResult.objects.filter(
                retest_state=CheckResult.RetestResult.FIXED
            ).count(),
        ),
    ]


def get_policy_progress_metrics() -> list[ProgressMetric]:
    """Return policy progress metrics"""
    now: datetime = timezone.now()
    start_date: datetime = now - timedelta(days=90)
    retested_audits: QuerySet[Audit] = Audit.objects.filter(retest_date__gte=start_date)
    retested_audits_count: int = retested_audits.count()
    fixed_audits: QuerySet[Audit] = retested_audits.filter(
        case__recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION
    )
    fixed_audits_count: int = fixed_audits.count()
    compliant_audits: QuerySet[Audit] = retested_audits.filter(
        case__compliance__statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT
    )
    compliant_audits_count: int = compliant_audits.count()
    check_results_of_last_90_days: QuerySet[CheckResult] = CheckResult.objects.filter(
        audit__retest_date__gte=start_date,
        page__retest_page_missing_date=None,
        page__is_deleted=False,
    )
    fixed_check_results_count: int = (
        check_results_of_last_90_days.filter(check_result_state="error")
        .filter(retest_state="fixed")
        .count()
    )
    total_check_results_count: int = (
        check_results_of_last_90_days.filter(check_result_state="error")
        .exclude(retest_state="not-retested")
        .count()
    )

    fixed_statement_issues_count, statement_issues_count = count_statement_issues(
        retested_audits
    )

    return [
        ProgressMetric(
            label="Websites compliant after retest in the last 90 days",
            partial_count=fixed_audits_count,
            total_count=retested_audits_count,
        ),
        ProgressMetric(
            label="Statements compliant after retest in the last 90 days",
            partial_count=compliant_audits_count,
            total_count=retested_audits_count,
        ),
        ProgressMetric(
            label="Website accessibility issues fixed in the last 90 days",
            partial_count=fixed_check_results_count,
            total_count=total_check_results_count,
        ),
        ProgressMetric(
            label="Statement issues fixed in the last 90 days",
            partial_count=fixed_statement_issues_count,
            total_count=statement_issues_count,
        ),
    ]


def get_equality_body_cases_metric() -> EqualityBodyCasesMetric:
    """Return numbers of cases completed or in progress with equality body"""
    thirteen_month_start_date: datetime = get_first_of_this_month_last_year()
    last_year_cases: QuerySet[Case] = Case.objects.filter(
        created__gte=thirteen_month_start_date
    )
    return EqualityBodyCasesMetric(
        label="Cases completed with equalities bodies in last year",
        completed_count=last_year_cases.filter(
            enforcement_body_pursuing="yes-completed"
        ).count(),
        in_progress_count=last_year_cases.filter(
            enforcement_body_pursuing="yes-in-progress"
        ).count(),
    )


def get_policy_yearly_metrics() -> list[YearlyMetric]:
    """Return policy yearly metrics"""
    thirteen_month_start_date: datetime = get_first_of_this_month_last_year()

    thirteen_month_retested_audits: QuerySet[Audit] = Audit.objects.filter(
        retest_date__gte=thirteen_month_start_date
    )
    thirteen_month_website_initial_compliant: QuerySet[Audit] = (
        thirteen_month_retested_audits.filter(
            case__compliance__website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT
        )
    )
    thirteen_month_statement_initial_compliant: QuerySet[Audit] = (
        thirteen_month_retested_audits.filter(
            case__compliance__statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT
        )
    )
    thirteen_month_final_no_action: QuerySet[Audit] = (
        thirteen_month_retested_audits.filter(
            case__recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION
        )
    )
    thirteen_month_statement_final_compliant: QuerySet[Audit] = (
        thirteen_month_retested_audits.filter(
            case__compliance__statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT
        )
    )

    retested_by_month: Timeseries = Timeseries(
        label="Cases",
        datapoints=group_timeseries_data_by_month(
            queryset=thirteen_month_retested_audits,
            date_column_name="retest_date",
            start_date=thirteen_month_start_date,
        ),
    )
    website_initial_compliant_by_month: Timeseries = Timeseries(
        label="Initially acceptable",
        datapoints=group_timeseries_data_by_month(
            queryset=thirteen_month_website_initial_compliant,
            date_column_name="retest_date",
            start_date=thirteen_month_start_date,
        ),
    )
    statement_initial_compliant_by_month: Timeseries = Timeseries(
        label="Initially compliant",
        datapoints=group_timeseries_data_by_month(
            queryset=thirteen_month_statement_initial_compliant,
            date_column_name="retest_date",
            start_date=thirteen_month_start_date,
        ),
    )
    final_no_action_by_month: Timeseries = Timeseries(
        label="Finally acceptable",
        datapoints=group_timeseries_data_by_month(
            queryset=thirteen_month_final_no_action,
            date_column_name="retest_date",
            start_date=thirteen_month_start_date,
        ),
    )
    statement_final_compliant_by_month: Timeseries = Timeseries(
        label="Finally compliant",
        datapoints=group_timeseries_data_by_month(
            queryset=thirteen_month_statement_final_compliant,
            date_column_name="retest_date",
            start_date=thirteen_month_start_date,
        ),
    )

    website_initial_ratio: Timeseries = convert_timeseries_pair_to_ratio(
        label="Initial",
        partial_timeseries=website_initial_compliant_by_month,
        total_timeseries=retested_by_month,
    )
    website_final_ratio: Timeseries = convert_timeseries_pair_to_ratio(
        label="Final",
        partial_timeseries=final_no_action_by_month,
        total_timeseries=retested_by_month,
    )
    statement_initial_ratio: Timeseries = convert_timeseries_pair_to_ratio(
        label="Initial",
        partial_timeseries=statement_initial_compliant_by_month,
        total_timeseries=retested_by_month,
    )
    statement_final_ratio: Timeseries = convert_timeseries_pair_to_ratio(
        label="Final",
        partial_timeseries=statement_final_compliant_by_month,
        total_timeseries=retested_by_month,
    )

    return [
        YearlyMetric(
            label="Proportion of websites which are acceptable",
            html_table=build_html_table(
                columns=[
                    retested_by_month,
                    website_initial_compliant_by_month,
                    final_no_action_by_month,
                ],
            ),
            chart=build_yearly_metric_chart(
                lines=[website_initial_ratio, website_final_ratio],
                y_axis_percent=True,
            ),
        ),
        YearlyMetric(
            label="Proportion of accessibility statements which are compliant",
            html_table=build_html_table(
                columns=[
                    retested_by_month,
                    statement_initial_compliant_by_month,
                    statement_final_compliant_by_month,
                ],
            ),
            chart=build_yearly_metric_chart(
                lines=[statement_initial_ratio, statement_final_ratio],
                y_axis_percent=True,
            ),
        ),
    ]


def get_report_progress_metrics() -> list[ThirtyDayMetric]:
    """Return report progress metrics"""
    thirty_days_ago: datetime = get_days_ago_timestamp(days=30)
    sixty_days_ago: datetime = get_days_ago_timestamp(days=60)

    return [
        ThirtyDayMetric(
            label="Published reports",
            last_30_day_count=S3Report.objects.filter(created__gte=thirty_days_ago)
            .filter(latest_published=True)
            .count(),
            previous_30_day_count=S3Report.objects.filter(
                created__gte=sixty_days_ago,
            )
            .filter(created__lt=thirty_days_ago)
            .filter(latest_published=True)
            .count(),
        ),
        ThirtyDayMetric(
            label="Report views",
            last_30_day_count=ReportVisitsMetrics.objects.filter(
                created__gte=thirty_days_ago
            ).count(),
            previous_30_day_count=ReportVisitsMetrics.objects.filter(
                created__gte=sixty_days_ago,
            )
            .filter(created__lt=thirty_days_ago)
            .count(),
        ),
        ThirtyDayMetric(
            label="Reports acknowledged",
            last_30_day_count=Case.objects.filter(
                report_acknowledged_date__gte=thirty_days_ago
            ).count(),
            previous_30_day_count=Case.objects.filter(
                report_acknowledged_date__gte=sixty_days_ago,
            )
            .filter(report_acknowledged_date__lt=thirty_days_ago)
            .count(),
        ),
    ]


def get_report_yearly_metrics() -> list[YearlyMetric]:
    """Return report yearly metrics"""
    start_date: datetime = get_first_of_this_month_last_year()
    published_reports_by_month: Timeseries = Timeseries(
        label="Published reports",
        datapoints=group_timeseries_data_by_month(
            queryset=S3Report.objects.filter(latest_published=True),
            date_column_name="created",
            start_date=start_date,
        ),
    )
    report_views_by_month: Timeseries = Timeseries(
        label="Report views",
        datapoints=group_timeseries_data_by_month(
            queryset=ReportVisitsMetrics.objects,
            date_column_name="created",
            start_date=start_date,
        ),
    )

    return [
        YearlyMetric(
            label="Reports published over the last year",
            html_table=build_html_table(columns=[published_reports_by_month]),
            chart=build_yearly_metric_chart(
                lines=[convert_timeseries_to_cumulative(published_reports_by_month)]
            ),
        ),
        YearlyMetric(
            label="Reports views over the last year",
            html_table=build_html_table(columns=[report_views_by_month]),
            chart=build_yearly_metric_chart(lines=[report_views_by_month]),
        ),
    ]
