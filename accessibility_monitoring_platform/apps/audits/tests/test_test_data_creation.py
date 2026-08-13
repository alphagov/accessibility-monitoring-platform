"""Test creation of test data"""

import pytest

from ...simplified.models import SimplifiedCase
from ..models import AuditOverview, WcagAudit
from .create_test_data import create_case_and_compliance

ORGANISATION_NAME: str = "Organisation name one"


@pytest.mark.django_db
def test_create_case_and_compliance_no_args():
    """Test cretaion of case and compliance with no arguments"""
    simplified_case: SimplifiedCase = create_case_and_compliance()

    assert isinstance(simplified_case, SimplifiedCase)
    assert isinstance(simplified_case.audit_overview, AuditOverview)


@pytest.mark.django_db
def test_create_case_and_compliance():
    """Test cretaion of case and compliance with mix of arguments"""
    simplified_case: SimplifiedCase = create_case_and_compliance(
        organisation_name=ORGANISATION_NAME,
        website_compliance_state_12_week=WcagAudit.WebsiteCompliance.COMPLIANT,
    )

    assert simplified_case.organisation_name == ORGANISATION_NAME
    assert (
        simplified_case.audit_overview.first_twelve_week_wcag_audit.compliance_state
        == WcagAudit.WebsiteCompliance.COMPLIANT
    )
