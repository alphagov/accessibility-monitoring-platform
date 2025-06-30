"""
Test forms of cases app
"""

from datetime import date, datetime

import pytest
from django.contrib.auth.models import User

from ...common.models import Boolean
from ...simplified.models import CaseCompliance, CaseStatus, SimplifiedCase
from ...simplified.utils import create_case_and_compliance
from ..forms import ExportCreateForm
from ..models import Export

CUTOFF_DATE: date = date(2024, 3, 20)
CUTOFF_DATETIME: date = datetime(2024, 3, 20, 1, 2, 3)


def create_exportable_case() -> SimplifiedCase:
    """Create a case which can be exported"""
    user: User = User.objects.create()
    simplified_case: SimplifiedCase = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=SimplifiedCase.ReportApprovedStatus.APPROVED,
        report_sent_date=CUTOFF_DATETIME,
        report_acknowledged_date=CUTOFF_DATETIME,
        twelve_week_update_requested_date=CUTOFF_DATETIME,
        twelve_week_correspondence_acknowledged_date=CUTOFF_DATETIME,
        compliance_email_sent_date=CUTOFF_DATE,
        case_completed=SimplifiedCase.CaseCompleted.COMPLETE_SEND,
    )
    simplified_case.update_case_status()
    return simplified_case


@pytest.mark.django_db
def test_clean_case_close_form_duplicate_export():
    """Tests export checked for duplicate cutoff date"""
    simplified_case: SimplifiedCase = create_exportable_case()

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": SimplifiedCase.EnforcementBody.EHRC,
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
        },
    )

    assert form.is_valid()

    Export.objects.create(cutoff_date=CUTOFF_DATE, exporter=simplified_case.auditor)

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": SimplifiedCase.EnforcementBody.EHRC,
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"cutoff_date": ["Export for this date already exists"]}

    simplified_case.enforcement_body = SimplifiedCase.EnforcementBody.ECNI
    simplified_case.save()

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": SimplifiedCase.EnforcementBody.ECNI,
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
        },
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_clean_case_close_form_no_matching_cases():
    """Tests export checked for matching cases - none found"""
    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": SimplifiedCase.EnforcementBody.EHRC,
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"cutoff_date": ["There are no cases to export"]}


@pytest.mark.django_db
def test_clean_case_close_form_ecni():
    """Tests export checked for ECNI cases"""
    simplified_case: SimplifiedCase = create_exportable_case()
    simplified_case.enforcement_body = SimplifiedCase.EnforcementBody.ECNI
    simplified_case.save()

    assert simplified_case.status == SimplifiedCase.Status.CASE_CLOSED_WAITING_TO_SEND

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": SimplifiedCase.EnforcementBody.ECNI,
            "cutoff_date_0": CUTOFF_DATE.day,
            "cutoff_date_1": CUTOFF_DATE.month,
            "cutoff_date_2": CUTOFF_DATE.year,
        },
        instance=Export(enforcement_body=SimplifiedCase.EnforcementBody.ECNI),
    )

    assert form.is_valid()
