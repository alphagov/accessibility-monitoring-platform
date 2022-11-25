"""
Test - common utility functions
"""
from typing import Dict, List, Tuple, Union
import pytest

from datetime import date, datetime

from ...audits.models import Audit
from ...cases.models import Case

from ..metrics import (
    Timeseries,
    TimeseriesDatapoint,
    TimeseriesHtmlTable,
    calculate_current_month_progress,
    calculate_metric_progress,
    count_statement_issues,
    group_timeseries_data_by_month,
    build_html_table,
    FIRST_COLUMN_HEADER,
)

METRIC_LABEL: str = "Metric label"
FIRST_COLUMN_NAME: str = "Column one"
SECOND_COLUMN_NAME: str = "Column two"
COLUMN_NAMES: List[str] = [FIRST_COLUMN_HEADER] + [
    FIRST_COLUMN_NAME,
    SECOND_COLUMN_NAME,
]


@pytest.mark.parametrize(
    "day_of_month, this_month_value, last_month_value, expected_metric",
    [
        (
            31,
            15,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "under",
            },
        ),
        (
            31,
            45,
            30,
            {
                "expected_progress_difference": 50,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            1,
            5,
            30,
            {
                "expected_progress_difference": 416,
                "expected_progress_difference_label": "over",
            },
        ),
        (
            31,
            45,
            0,
            {},
        ),
    ],
)
def test_calculate_current_month_progress(
    day_of_month,
    this_month_value,
    last_month_value,
    expected_metric,
):
    """
    Test calculation of progress through current month
    """
    expected_metric["label"] = METRIC_LABEL
    expected_metric["this_month_value"] = this_month_value
    expected_metric["last_month_value"] = last_month_value

    assert expected_metric == calculate_current_month_progress(
        now=datetime(2022, 12, day_of_month),
        label=METRIC_LABEL,
        this_month_value=this_month_value,
        last_month_value=last_month_value,
    )


@pytest.mark.parametrize(
    "partial_count, total_count, expected_result",
    [
        (
            500,
            1000,
            {
                "label": METRIC_LABEL,
                "partial_count": 500,
                "total_count": 1000,
                "percentage": 50,
            },
        ),
        (
            333,
            1000,
            {
                "label": METRIC_LABEL,
                "partial_count": 333,
                "total_count": 1000,
                "percentage": 33,
            },
        ),
        (
            0,
            7,
            {
                "label": METRIC_LABEL,
                "partial_count": 0,
                "total_count": 7,
                "percentage": 0,
            },
        ),
    ],
)
def test_calculate_metric_progress(
    partial_count: int, total_count: int, expected_result: Dict[str, Union[str, int]]
):
    """Test the calculation of metric progress returns the correct values"""
    assert (
        calculate_metric_progress(
            label=METRIC_LABEL, partial_count=partial_count, total_count=total_count
        )
        == expected_result
    )


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
    """Test counting issues and fixed issues for accessibility statments"""
    assert count_statement_issues(audits=audits) == expected_result  # type: ignore


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
        TimeseriesDatapoint(datetime=date(2022, 1, 1), value=3),  # type: ignore
        TimeseriesDatapoint(datetime=date(2022, 2, 1), value=2),  # type: ignore
        TimeseriesDatapoint(datetime=date(2022, 4, 1), value=1),  # type: ignore
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
