"""
Test forms of cases app
"""

from datetime import date, datetime

import pytest
from django.contrib.auth.models import User

from ...cases.models import Boolean, Case, CaseCompliance, CaseStatus
from ...cases.utils import create_case_and_compliance
from ..forms import ExportCreateForm
from ..models import Export

TODAY: date = date.today()


def create_exportable_case() -> Case:
    """Create a case which can be exported"""
    user: User = User.objects.create()
    case: Case = create_case_and_compliance(
        home_page_url="https://www.website.com",
        organisation_name="org name",
        auditor=user,
        statement_compliance_state_initial=CaseCompliance.StatementCompliance.COMPLIANT,
        website_compliance_state_initial=CaseCompliance.WebsiteCompliance.COMPLIANT,
        report_review_status=Boolean.YES,
        report_approved_status=Case.ReportApprovedStatus.APPROVED,
        report_sent_date=datetime.now(),
        report_acknowledged_date=datetime.now(),
        twelve_week_update_requested_date=datetime.now(),
        twelve_week_correspondence_acknowledged_date=datetime.now(),
        compliance_email_sent_date=TODAY,
        case_completed=Case.CaseCompleted.COMPLETE_SEND,
    )
    return case


@pytest.mark.django_db
def test_clean_case_close_form_duplicate_export():
    """Tests export checked for duplicate cutoff date"""
    case: Case = create_exportable_case()

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": Case.EnforcementBody.EHRC,
            "cutoff_date_0": TODAY.day,
            "cutoff_date_1": TODAY.month,
            "cutoff_date_2": TODAY.year,
        },
    )

    assert form.is_valid()

    Export.objects.create(cutoff_date=TODAY, exporter=case.auditor)

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": Case.EnforcementBody.EHRC,
            "cutoff_date_0": TODAY.day,
            "cutoff_date_1": TODAY.month,
            "cutoff_date_2": TODAY.year,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"cutoff_date": ["Export for this date already exists"]}


@pytest.mark.django_db
def test_clean_case_close_form_no_matching_cases():
    """Tests export checked for matching cases - none found"""
    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": Case.EnforcementBody.EHRC,
            "cutoff_date_0": TODAY.day,
            "cutoff_date_1": TODAY.month,
            "cutoff_date_2": TODAY.year,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"cutoff_date": ["There are no cases to export"]}


@pytest.mark.django_db
def test_clean_case_close_form_ecni():
    """Tests export checked for ECNI cases"""
    case: Case = create_exportable_case()
    case.enforcement_body = Case.EnforcementBody.ECNI
    case.save()

    assert case.status.status == CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND

    form: ExportCreateForm = ExportCreateForm(
        data={
            "enforcement_body": Case.EnforcementBody.ECNI,
            "cutoff_date_0": TODAY.day,
            "cutoff_date_1": TODAY.month,
            "cutoff_date_2": TODAY.year,
        },
        instance=Export(enforcement_body=Case.EnforcementBody.ECNI),
    )

    assert form.is_valid()
