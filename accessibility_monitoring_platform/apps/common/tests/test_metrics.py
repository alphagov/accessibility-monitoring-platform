"""
Test - common utility functions
"""
import pytest
from typing import List, Tuple
from unittest.mock import patch

from datetime import date, datetime, timezone

from ...audits.models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    CHECK_RESULT_ERROR,
    RETEST_CHECK_RESULT_FIXED,
    TEST_TYPE_AXE,
)
from ...cases.models import Case, CASE_COMPLETED_NO_SEND

from ..metrics import (
    Timeseries,
    TimeseriesDatapoint,
    TimeseriesHtmlTable,
    count_statement_issues,
    group_timeseries_data_by_month,
    build_html_table,
    convert_timeseries_pair_to_ratio,
    convert_timeseries_to_cumulative,
    FIRST_COLUMN_HEADER,
    get_case_progress_metrics,
    ThirtyDayMetric,
    get_case_yearly_metrics,
    YearlyMetric,
    get_policy_total_metrics,
    TotalMetric,
)

METRIC_LABEL: str = "Metric label"
FIRST_COLUMN_NAME: str = "Column one"
SECOND_COLUMN_NAME: str = "Column two"
COLUMN_NAMES: List[str] = [FIRST_COLUMN_HEADER] + [
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


@pytest.mark.parametrize(
    "audits, expected_result",
    [
        ([Audit()], (0, 11)),
        ([Audit(declaration_state="not-present")], (0, 11)),
        ([Audit(declaration_state="present")], (0, 10)),
        (
            [
                Audit(
                    declaration_state="present",
                    audit_retest_declaration_state="present",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    declaration_state="not-present",
                    audit_retest_declaration_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(scope_state="not-present")], (0, 11)),
        ([Audit(scope_state="present")], (0, 10)),
        ([Audit(scope_state="present", audit_retest_scope_state="present")], (0, 10)),
        (
            [Audit(scope_state="not-present", audit_retest_scope_state="present")],
            (1, 11),
        ),
        ([Audit(compliance_state="not-present")], (0, 11)),
        ([Audit(compliance_state="present")], (0, 10)),
        (
            [
                Audit(
                    compliance_state="present", audit_retest_compliance_state="present"
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    compliance_state="not-present",
                    audit_retest_compliance_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(non_regulation_state="not-present")], (0, 11)),
        ([Audit(non_regulation_state="present")], (0, 10)),
        (
            [
                Audit(
                    non_regulation_state="present",
                    audit_retest_non_regulation_state="present",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    non_regulation_state="not-present",
                    audit_retest_non_regulation_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(preparation_date_state="not-present")], (0, 11)),
        ([Audit(preparation_date_state="present")], (0, 10)),
        (
            [
                Audit(
                    preparation_date_state="present",
                    audit_retest_preparation_date_state="present",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    preparation_date_state="not-present",
                    audit_retest_preparation_date_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(method_state="not-present")], (0, 11)),
        ([Audit(method_state="present")], (0, 10)),
        ([Audit(method_state="present", audit_retest_method_state="present")], (0, 10)),
        (
            [Audit(method_state="not-present", audit_retest_method_state="present")],
            (1, 11),
        ),
        ([Audit(review_state="not-present")], (0, 11)),
        ([Audit(review_state="present")], (0, 10)),
        ([Audit(review_state="present", audit_retest_review_state="present")], (0, 10)),
        (
            [Audit(review_state="not-present", audit_retest_review_state="present")],
            (1, 11),
        ),
        ([Audit(feedback_state="not-present")], (0, 11)),
        ([Audit(feedback_state="present")], (0, 10)),
        (
            [Audit(feedback_state="present", audit_retest_feedback_state="present")],
            (0, 10),
        ),
        (
            [
                Audit(
                    feedback_state="not-present", audit_retest_feedback_state="present"
                )
            ],
            (1, 11),
        ),
        ([Audit(contact_information_state="not-present")], (0, 11)),
        ([Audit(contact_information_state="present")], (0, 10)),
        (
            [
                Audit(
                    contact_information_state="present",
                    audit_retest_contact_information_state="present",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    contact_information_state="not-present",
                    audit_retest_contact_information_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(enforcement_procedure_state="not-present")], (0, 11)),
        ([Audit(enforcement_procedure_state="present")], (0, 10)),
        (
            [
                Audit(
                    enforcement_procedure_state="present",
                    audit_retest_enforcement_procedure_state="present",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    enforcement_procedure_state="not-present",
                    audit_retest_enforcement_procedure_state="present",
                )
            ],
            (1, 11),
        ),
        ([Audit(access_requirements_state="req-not-met")], (0, 11)),
        ([Audit(access_requirements_state="req-met")], (0, 10)),
        (
            [
                Audit(
                    access_requirements_state="req-met",
                    audit_retest_access_requirements_state="req-met",
                )
            ],
            (0, 10),
        ),
        (
            [
                Audit(
                    access_requirements_state="req-not-met",
                    audit_retest_access_requirements_state="req-met",
                )
            ],
            (1, 11),
        ),
        (
            [
                Audit(
                    access_requirements_state="req-not-met",
                    audit_retest_access_requirements_state="req-met",
                ),
                Audit(scope_state="not-present", audit_retest_scope_state="present"),
                Audit(scope_state="not-present", audit_retest_scope_state="present"),
            ],
            (3, 33),
        ),
        (
            [
                Audit(
                    access_requirements_state="req-not-met",
                    audit_retest_access_requirements_state="req-met",
                    scope_state="not-present",
                    audit_retest_scope_state="present",
                    compliance_state="not-present",
                    audit_retest_compliance_state="present",
                ),
            ],
            (3, 11),
        ),
    ],
)
def test_count_statement_issues(audits: List[Audit], expected_result: Tuple[int, int]):
    """Test counting issues and fixed issues for accessibility statements"""
    assert count_statement_issues(audits=audits) == expected_result


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
                rows=[["January 2022", "1", "2"]],
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
                ],
            ),
        ),
    ],
)
def test_build_html_table(
    columns: List[Timeseries],
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
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 6, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2022, 1, 1, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 16, tzinfo=timezone.utc),
    )

    case_progress_metrics: List[ThirtyDayMetric] = get_case_progress_metrics()

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
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 5, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 5, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2021, 12, 6, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
    )
    Case.objects.create(
        created=datetime(2022, 1, 1, tzinfo=timezone.utc),
        testing_details_complete_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
        report_sent_date=datetime(2021, 12, 6, tzinfo=timezone.utc),
        completed_date=datetime(2021, 12, 16, tzinfo=timezone.utc),
    )

    case_yearly_metrics: List[YearlyMetric] = get_case_yearly_metrics()

    assert len(case_yearly_metrics)
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
        case_completed=CASE_COMPLETED_NO_SEND,
    )
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit)
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(type=TEST_TYPE_AXE)
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
    )
    CheckResult.objects.create(
        audit=audit,
        page=page,
        wcag_definition=wcag_definition,
        check_result_state=CHECK_RESULT_ERROR,
        retest_state=RETEST_CHECK_RESULT_FIXED,
    )

    assert get_policy_total_metrics() == [
        TotalMetric(label="Total reports sent", total=2),
        TotalMetric(label="Total cases closed", total=1),
        TotalMetric(label="Total number of accessibility issues found", total=2),
        TotalMetric(label="Total number of accessibility issues fixed", total=1),
    ]
