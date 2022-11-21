"""
Test - common utility functions
"""
from typing import Dict, List, Tuple, Union
import pytest
from unittest.mock import patch

from datetime import datetime

from ...audits.models import Audit

from ..metrics import (
    calculate_current_month_progress,
    calculate_metric_progress,
    count_statement_issues,
)

METRIC_LABEL: str = "Metric label"


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
@patch("accessibility_monitoring_platform.apps.common.metrics.timezone")
def test_calculate_current_month_progress(
    mock_timezone,
    day_of_month,
    this_month_value,
    last_month_value,
    expected_metric,
):
    """
    Test calculation of progress through current month
    """
    mock_timezone.now.return_value = datetime(2022, 12, day_of_month)
    expected_metric["label"] = METRIC_LABEL
    expected_metric["this_month_value"] = this_month_value
    expected_metric["last_month_value"] = last_month_value

    assert expected_metric == calculate_current_month_progress(
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
