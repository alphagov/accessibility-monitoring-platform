"""
Test forms of cases app
"""
import pytest
from typing import List, Tuple

from ..forms import CaseSearchForm, CaseDetailUpdateForm, CaseReportDetailsUpdateForm
from ..models import Case

USER_CHOICES: List[Tuple[str, str]] = [("", "-----"), ("none", "Unassigned")]
HOME_PAGE_URL: str = "https://example.com"


@pytest.mark.parametrize("fieldname", ["auditor", "reviewer"])
@pytest.mark.django_db
def test_case_search_form_user_field_includes_choice_of_unassigned(fieldname):
    """Tests if user choice field includes empty and unassigned options"""
    form: CaseSearchForm = CaseSearchForm()
    assert fieldname in form.fields
    assert form.fields[fieldname].choices == USER_CHOICES


@pytest.mark.parametrize(
    "testing_methodology, report_methodology, expected_valid",
    [
        ("platform", "platform", True),
        ("spreadsheet", "platform", False),
        ("platform", "odt", True),
        ("spreadsheet", "odt", True),
    ],
)
@pytest.mark.django_db
def test_case_report_detail_update_form_methodology_validation(
    testing_methodology, report_methodology, expected_valid
):
    """Tests testing and report methodology cross-field validation"""
    case: Case = Case.objects.create()
    form: CaseDetailUpdateForm = CaseDetailUpdateForm(
        data={
            "version": case.version,
            "home_page_url": HOME_PAGE_URL,
            "enforcement_body": "ehrc",
            "testing_methodology": testing_methodology,
            "report_methodology": report_methodology,
        },
        instance=case,
    )

    if expected_valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert form.errors == {
            "testing_methodology": [
                "Testing methodology has to be platform for reporting methodology to be platform",
            ],
            "report_methodology": [
                "For reporting methodology to be platform, testing methodology has to be platform",
            ],
        }


@pytest.mark.parametrize(
    "report_review_status, report_draft_url, expected_valid",
    [
        ("ready-to-review", "", False),
        ("not-started", "", True),
        ("in-progress", "", True),
        ("ready-to-review", "https://report-draft-url.com", True),
        ("not-started", "https://report-draft-url.com", True),
        ("in-progress", "https://report-draft-url.com", True),
    ],
)
@pytest.mark.django_db
def test_case_detail_update_form_review_status_url_validation(
    report_review_status, report_draft_url, expected_valid
):
    """
    Tests report review status of ready to review makes report draft url mandatory
    """
    case: Case = Case.objects.create()
    form: CaseReportDetailsUpdateForm = CaseReportDetailsUpdateForm(
        data={
            "version": case.version,
            "report_review_status": report_review_status,
            "report_draft_url": report_draft_url,
        },
        instance=case,
    )

    if expected_valid:
        assert form.is_valid()
    else:
        assert not form.is_valid()
        assert form.errors == {
            "report_review_status": [
                "Report cannot be ready to be reviewed without a link to report draft",
            ],
            "report_draft_url": [
                "Add link to report draft, if report is ready to be reviewed",
            ],
        }
