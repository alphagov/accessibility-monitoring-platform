"""
Test - common utility functions
"""

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)
from ...cases.models import Case, CaseCompliance
from ...cases.utils import create_case_and_compliance
from ...reports.models import ReportVisitsMetrics
from ...s3_read_write.models import S3Report
from ..chart import Timeseries, TimeseriesDatapoint
from ..metrics import (
    FIRST_COLUMN_HEADER,
    EqualityBodyCasesMetric,
    ProgressMetric,
    ThirtyDayMetric,
    TimeseriesHtmlTable,
    TotalMetric,
    YearlyMetric,
    build_html_table,
    convert_timeseries_pair_to_ratio,
    convert_timeseries_to_cumulative,
    count_statement_issues,
    get_case_progress_metrics,
    get_case_yearly_metrics,
    get_equality_body_cases_metric,
    get_policy_progress_metrics,
    get_policy_total_metrics,
    get_policy_yearly_metrics,
    get_report_progress_metrics,
    get_report_yearly_metrics,
    group_timeseries_data_by_month,
)

METRIC_LABEL: str = "Metric label"
FIRST_COLUMN_NAME: str = "Column one"
SECOND_COLUMN_NAME: str = "Column two"
COLUMN_NAMES: list[str] = [FIRST_COLUMN_HEADER] + [
    FIRST_COLUMN_NAME,
    SECOND_COLUMN_NAME,
]


def test_thirty_day_metric():
    """Test thirty day metric class"""
    thirty_day_metric: ThirtyDayMetric = ThirtyDayMetric(
        label=METRIC_LABEL,
        last_30_day_count=30,
        previous_30_day_count=15,
    )
    assert thirty_day_metric.label == METRIC_LABEL
    assert thirty_day_metric.last_30_day_count == 30
    assert thirty_day_metric.previous_30_day_count == 15


@pytest.mark.parametrize(
    "last_30_day_count, previous_30_day_count, expected_progress_label",
    [(10, 20, "under"), (2, 1, "over"), (2, 2, "over")],
)
def test_thirty_day_metric_progress_label(
    last_30_day_count, previous_30_day_count, expected_progress_label
):
    """Test progress label derived correctly"""
    thirty_day_metric: ThirtyDayMetric = ThirtyDayMetric(
        label=METRIC_LABEL,
        last_30_day_count=last_30_day_count,
        previous_30_day_count=previous_30_day_count,
    )
    assert thirty_day_metric.progress_label == expected_progress_label


@pytest.mark.parametrize(
    "last_30_day_count, previous_30_day_count, expected_progress_percentage",
    [(6, 9, 34), (10, 8, 25), (2, 1, 100), (2, 2, 0)],
)
def test_thirty_day_metric_progress_percentage(
    last_30_day_count, previous_30_day_count, expected_progress_percentage
):
    """Test progress percentage derived correctly"""
    thirty_day_metric: ThirtyDayMetric = ThirtyDayMetric(
        label=METRIC_LABEL,
        last_30_day_count=last_30_day_count,
        previous_30_day_count=previous_30_day_count,
    )
    assert thirty_day_metric.progress_percentage == expected_progress_percentage


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statement_check_result_params, expected_fixed, expected_total",
    [
        ({}, 0, 0),
        ({"check_result_state": "yes"}, 0, 0),
        ({"check_result_state": "no"}, 0, 1),
        ({"check_result_state": "yes", "retest_state": "yes"}, 0, 0),
        ({"check_result_state": "no", "retest_state": "yes"}, 1, 1),
        ({"check_result_state": "no", "retest_state": "no"}, 0, 1),
    ],
)
def test_count_statement_issues(
    statement_check_result_params: dict[str, str],
    expected_fixed: int,
    expected_total: int,
):
    """Test counting issues and fixed issues for accessibility statements"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    StatementCheckResult.objects.create(
        **statement_check_result_params,
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
    )

    assert count_statement_issues(audits=Audit.objects.all()) == (
        expected_fixed,
        expected_total,
    )


@pytest.mark.django_db
def test_group_timeseries_data_by_month():
    """
    Test counting objects and grouping a queryset with a date/datetime field by
    month
    """
    Case.objects.create(case_details_complete_date=date(2022, 1, 1))
    Case.objects.create(case_details_complete_date=date(2022, 1, 2))
    Case.objects.create(case_details_complete_date=date(2022, 1, 3))
    Case.objects.create(case_details_complete_date=date(2022, 2, 4))
    Case.objects.create(case_details_complete_date=date(2022, 2, 5))
    Case.objects.create(case_details_complete_date=date(2022, 4, 6))

    assert group_timeseries_data_by_month(
        queryset=Case.objects,
        date_column_name="case_details_complete_date",
        start_date=datetime(2022, 1, 1),
    ) == [
        TimeseriesDatapoint(
            datetime=datetime(2022, 1, 1, tzinfo=timezone.utc), value=3
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 2, 1, tzinfo=timezone.utc), value=2
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 3, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 4, 1, tzinfo=timezone.utc), value=1
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 5, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 6, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 7, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 8, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 9, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 10, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 11, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2022, 12, 1, tzinfo=timezone.utc), value=0
        ),
        TimeseriesDatapoint(
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc), value=0
        ),
    ]


@pytest.mark.parametrize(
    "columns, expected_result",
    [
        (
            [
                Timeseries(
                    label=FIRST_COLUMN_NAME,
                    datapoints=[
                        TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=1)
                    ],
                ),
                Timeseries(
                    label=SECOND_COLUMN_NAME,
                    datapoints=[
                        TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=2)
                    ],
                ),
            ],
            TimeseriesHtmlTable(
                column_names=COLUMN_NAMES,
                rows=[["January 2022", "1", "2"], ["Totals", "1", "2"]],
            ),
        ),
        (
            [
                Timeseries(
                    label=FIRST_COLUMN_NAME,
                    datapoints=[
                        TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=1),
                        TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=3),
                        TimeseriesDatapoint(datetime=datetime(2022, 4, 1), value=5),
                        TimeseriesDatapoint(datetime=datetime(2022, 7, 1), value=7),
                    ],
                ),
                Timeseries(
                    label=SECOND_COLUMN_NAME,
                    datapoints=[
                        TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=2),
                        TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=4),
                        TimeseriesDatapoint(datetime=datetime(2022, 4, 1), value=6),
                        TimeseriesDatapoint(datetime=datetime(2022, 8, 1), value=8),
                    ],
                ),
            ],
            TimeseriesHtmlTable(
                column_names=COLUMN_NAMES,
                rows=[
                    ["January 2022", "1", "2"],
                    ["February 2022", "3", ""],
                    ["March 2022", "", "4"],
                    ["April 2022", "5", "6"],
                    ["July 2022", "7", ""],
                    ["August 2022", "", "8"],
                    ["Totals", "16", "20"],
                ],
            ),
        ),
    ],
)
def test_build_html_table(
    columns: list[Timeseries],
    expected_result: TimeseriesHtmlTable,
):
    """Test merging multiple data series into a single HTML table context"""
    assert build_html_table(columns=columns) == expected_result


def test_convert_timeseries_pair_to_ratio():
    """
    Test merging two timeseries into one containing the ratios of the values
    in both.
    """
    partial_timeseries: Timeseries = Timeseries(
        label="Partial",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=1),
            TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=2),
            TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=3),
        ],
    )
    total_timeseries: Timeseries = Timeseries(
        label="Total",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=2),
            TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=3),
            TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=4),
        ],
    )
    assert convert_timeseries_pair_to_ratio(
        label="Ratios",
        partial_timeseries=partial_timeseries,
        total_timeseries=total_timeseries,
    ) == Timeseries(
        label="Ratios",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=50),
            TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=66),
            TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=75),
        ],
    )


def test_convert_timeseries_to_cumulative():
    """Test converting the datapoints of a timeseries to be cumulative"""
    assert convert_timeseries_to_cumulative(
        Timeseries(
            label="Label",
            datapoints=[
                TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=1),
                TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=3),
                TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=5),
            ],
        )
    ) == Timeseries(
        label="Label",
        datapoints=[
            TimeseriesDatapoint(datetime=datetime(2022, 1, 1), value=1),
            TimeseriesDatapoint(datetime=datetime(2022, 2, 1), value=4),
            TimeseriesDatapoint(datetime=datetime(2022, 3, 1), value=9),
        ],
    )


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_get_case_progress_metrics(mock_date):
    """Test case progress metrics returned"""
    mock_date.today.return_value = date(2022, 1, 20)

    Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 6, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2022, 1, 1, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 16, tzinfo=timezone.utc),
    )

    case_progress_metrics: list[ThirtyDayMetric] = get_case_progress_metrics()

    assert len(case_progress_metrics) == 4
    assert case_progress_metrics == [
        ThirtyDayMetric(
            label="Cases created", last_30_day_count=1, previous_30_day_count=2
        ),
        ThirtyDayMetric(
            label="Tests completed", last_30_day_count=4, previous_30_day_count=0
        ),
        ThirtyDayMetric(
            label="Reports sent", last_30_day_count=2, previous_30_day_count=2
        ),
        ThirtyDayMetric(
            label="Cases closed", last_30_day_count=1, previous_30_day_count=3
        ),
    ]


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_get_case_yearly_metrics(mock_datetime):
    """Test case yearly metrics returned"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 6, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2022, 1, 1, tzinfo=timezone.utc),
        reporting_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 16, tzinfo=timezone.utc),
    )

    case_yearly_metrics: list[YearlyMetric] = get_case_yearly_metrics()

    assert len(case_yearly_metrics) == 4
    assert case_yearly_metrics[0].label == "Cases created over the last year"
    assert case_yearly_metrics[0].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Cases created"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "1"],
            ["December 2021", "2"],
            ["January 2022", "1"],
            ["Total", "4"],
        ],
    )
    assert case_yearly_metrics[1].label == "Tests completed over the last year"
    assert case_yearly_metrics[1].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Tests completed"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "0"],
            ["December 2021", "0"],
            ["January 2022", "4"],
            ["Total", "4"],
        ],
    )
    assert case_yearly_metrics[2].label == "Reports sent over the last year"
    assert case_yearly_metrics[2].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Reports sent"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "0"],
            ["December 2021", "2"],
            ["January 2022", "2"],
            ["Total", "4"],
        ],
    )
    assert case_yearly_metrics[3].label == "Cases completed over the last year"
    assert case_yearly_metrics[3].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Cases completed"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "0"],
            ["December 2021", "3"],
            ["January 2022", "1"],
            ["Total", "4"],
        ],
    )


@pytest.mark.django_db
def test_get_policy_total_metrics():
    """Test policy total metrics returned"""
    case: Case = Case.objects.create(
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        case_completed=Case.CaseCompleted.COMPLETE_NO_SEND,
    )
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
    )

    assert get_policy_total_metrics() == [
        TotalMetric(label="Total reports sent", total=2),
        TotalMetric(label="Total cases closed", total=1),
        TotalMetric(label="Total number of accessibility issues found", total=2),
        TotalMetric(label="Total number of accessibility issues fixed", total=1),
    ]


@pytest.mark.parametrize(
    "partial_count, total_count, expected_percentage",
    [
        (5, 10, 50),
        (0, 10, 0),
        (5, 0, 0),
        (5, 1, 500),
    ],
)
def test_progress_metric_percentage(
    partial_count: int, total_count: int, expected_percentage: int
):
    """iTest progress metric calculates percentage"""
    progress_metric: ProgressMetric = ProgressMetric(
        label="label",
        partial_count=partial_count,
        total_count=total_count,
    )

    assert progress_metric.percentage == expected_percentage


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_get_policy_progress_metrics(mock_datetime):
    """Test policy progress metrics"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    case: Case = Case.objects.create(
        recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION
    )
    audit: Audit = Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
    )
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
        check_result_state=StatementCheckResult.Result.NO,
        retest_state=StatementCheckResult.Result.YES,
    )

    assert get_policy_progress_metrics() == [
        ProgressMetric(
            label="Websites compliant after retest in the last 90 days",
            partial_count=1,
            total_count=1,
        ),
        ProgressMetric(
            label="Statements compliant after retest in the last 90 days",
            partial_count=0,
            total_count=1,
        ),
        ProgressMetric(
            label="Website accessibility issues fixed in the last 90 days",
            partial_count=1,
            total_count=2,
        ),
        ProgressMetric(
            label="Statement issues fixed in the last 90 days",
            partial_count=1,
            total_count=1,
        ),
    ]


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_get_policy_progress_metrics_excludes_missing_pages(mock_datetime):
    """Test policy progress metrics excludes missing pages"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    case: Case = Case.objects.create(
        recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION
    )
    audit: Audit = Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )
    page: Page = Page.objects.create(
        audit=audit, retest_page_missing_date=datetime(2022, 1, 2, tzinfo=timezone.utc)
    )
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.NOT_FIXED,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CheckResult.Result.ERROR,
        retest_state=CheckResult.RetestResult.FIXED,
    )
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
        check_result_state=StatementCheckResult.Result.NO,
        retest_state=StatementCheckResult.Result.YES,
    )

    assert get_policy_progress_metrics() == [
        ProgressMetric(
            label="Websites compliant after retest in the last 90 days",
            partial_count=1,
            total_count=1,
        ),
        ProgressMetric(
            label="Statements compliant after retest in the last 90 days",
            partial_count=0,
            total_count=1,
        ),
        ProgressMetric(
            label="Website accessibility issues fixed in the last 90 days",
            partial_count=0,
            total_count=0,
        ),
        ProgressMetric(
            label="Statement issues fixed in the last 90 days",
            partial_count=1,
            total_count=1,
        ),
    ]


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_get_equality_body_cases_metric(mock_datetime):
    """Test equality body cases metric"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)
    Case.objects.create(enforcement_body_pursuing="yes-completed")
    Case.objects.create(enforcement_body_pursuing="yes-completed")
    Case.objects.create(enforcement_body_pursuing="yes-in-progress")

    assert get_equality_body_cases_metric() == EqualityBodyCasesMetric(
        label="Cases completed with equalities bodies in last year",
        completed_count=2,
        in_progress_count=1,
    )


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_get_policy_yearly_metrics(mock_datetime):
    """Test policy yearly metrics returned"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    case: Case = create_case_and_compliance(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )
    case: Case = create_case_and_compliance(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc),
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )
    case: Case = create_case_and_compliance(
        created=datetime(2021, 12, 6, tzinfo=timezone.utc),
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        recommendation_for_enforcement=Case.RecommendationForEnforcement.NO_FURTHER_ACTION,
    )
    Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )
    case: Case = create_case_and_compliance(
        created=datetime(2022, 1, 1, tzinfo=timezone.utc),
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        statement_compliance_state_12_week=CaseCompliance.StatementCompliance.COMPLIANT,
    )
    Audit.objects.create(
        case=case, retest_date=datetime(2022, 1, 20, tzinfo=timezone.utc)
    )

    policy_yearly_metrics: list[YearlyMetric] = get_policy_yearly_metrics()

    assert len(policy_yearly_metrics) == 2
    assert (
        policy_yearly_metrics[0].label == "Proportion of websites which are acceptable"
    )
    assert policy_yearly_metrics[0].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Cases", "Initially acceptable", "Finally acceptable"],
        rows=[
            ["January 2021", "0", "0", "0"],
            ["February 2021", "0", "0", "0"],
            ["March 2021", "0", "0", "0"],
            ["April 2021", "0", "0", "0"],
            ["May 2021", "0", "0", "0"],
            ["June 2021", "0", "0", "0"],
            ["July 2021", "0", "0", "0"],
            ["August 2021", "0", "0", "0"],
            ["September 2021", "0", "0", "0"],
            ["October 2021", "0", "0", "0"],
            ["November 2021", "0", "0", "0"],
            ["December 2021", "0", "0", "0"],
            ["January 2022", "4", "4", "2"],
            ["Totals", "4", "4", "2"],
        ],
    )
    assert (
        policy_yearly_metrics[1].label
        == "Proportion of accessibility statements which are compliant"
    )
    assert policy_yearly_metrics[1].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Cases", "Initially compliant", "Finally compliant"],
        rows=[
            ["January 2021", "0", "0", "0"],
            ["February 2021", "0", "0", "0"],
            ["March 2021", "0", "0", "0"],
            ["April 2021", "0", "0", "0"],
            ["May 2021", "0", "0", "0"],
            ["June 2021", "0", "0", "0"],
            ["July 2021", "0", "0", "0"],
            ["August 2021", "0", "0", "0"],
            ["September 2021", "0", "0", "0"],
            ["October 2021", "0", "0", "0"],
            ["November 2021", "0", "0", "0"],
            ["December 2021", "0", "0", "0"],
            ["January 2022", "4", "1", "1"],
            ["Totals", "4", "1", "1"],
        ],
    )


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.date")
def test_get_report_progress_metrics(mock_date):
    """Test report progress metrics returned"""
    mock_date.today.return_value = date(2022, 1, 20)

    Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        report_acknowledged_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        report_acknowledged_date=datetime(2021, 12, 1, tzinfo=timezone.utc),
    )
    case: Case = Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
        report_acknowledged_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )
    s3_report: S3Report = S3Report.objects.create(
        case=case,
        version=1,
        latest_published=True,
    )
    S3Report.objects.filter(id=s3_report.id).update(
        created=datetime(2021, 12, 31, tzinfo=timezone.utc),
    )
    report_visits_metrics: ReportVisitsMetrics = ReportVisitsMetrics.objects.create(
        case=case,
    )
    ReportVisitsMetrics.objects.filter(id=report_visits_metrics.id).update(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc)
    )

    assert get_report_progress_metrics() == [
        ThirtyDayMetric(
            label="Published reports", last_30_day_count=1, previous_30_day_count=0
        ),
        ThirtyDayMetric(
            label="Report views", last_30_day_count=0, previous_30_day_count=1
        ),
        ThirtyDayMetric(
            label="Reports acknowledged", last_30_day_count=1, previous_30_day_count=2
        ),
    ]


@pytest.mark.django_db
@patch("accessibility_monitoring_platform.apps.common.utils.timezone")
def test_get_report_yearly_metrics(mock_datetime):
    """Test report yearly metrics returned"""
    mock_datetime.now.return_value = datetime(2022, 1, 20, tzinfo=timezone.utc)

    case: Case = Case.objects.create(
        created=datetime(2021, 11, 5, tzinfo=timezone.utc),
    )
    s3_report: S3Report = S3Report.objects.create(
        case=case,
        version=1,
        latest_published=True,
    )
    S3Report.objects.filter(id=s3_report.id).update(
        created=datetime(2021, 12, 31, tzinfo=timezone.utc),
    )
    report_visits_metrics: ReportVisitsMetrics = ReportVisitsMetrics.objects.create(
        case=case,
    )
    ReportVisitsMetrics.objects.filter(id=report_visits_metrics.id).update(
        created=datetime(2022, 1, 5, tzinfo=timezone.utc)
    )

    report_yearly_metrics: list[YearlyMetric] = get_report_yearly_metrics()

    assert len(report_yearly_metrics) == 2
    assert report_yearly_metrics[0].label == "Reports published over the last year"
    assert report_yearly_metrics[0].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Published reports"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "0"],
            ["December 2021", "1"],
            ["January 2022", "0"],
            ["Total", "1"],
        ],
    )
    assert report_yearly_metrics[1].label == "Reports views over the last year"
    assert report_yearly_metrics[1].html_table == TimeseriesHtmlTable(
        column_names=["Month", "Report views"],
        rows=[
            ["January 2021", "0"],
            ["February 2021", "0"],
            ["March 2021", "0"],
            ["April 2021", "0"],
            ["May 2021", "0"],
            ["June 2021", "0"],
            ["July 2021", "0"],
            ["August 2021", "0"],
            ["September 2021", "0"],
            ["October 2021", "0"],
            ["November 2021", "0"],
            ["December 2021", "0"],
            ["January 2022", "1"],
            ["Total", "1"],
        ],
    )
