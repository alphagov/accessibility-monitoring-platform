""" Test build email template context """

from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from ...audits.models import Audit, Retest
from ...cases.models import Case
from ..email_template_utils import get_email_template_context


@pytest.mark.django_db
def test_get_email_template_context_new_case():
    """Test get_email_template_context for new Case"""
    case: Case = Case.objects.create()
    email_template_context: dict[str, Any] = get_email_template_context(case=case)

    assert "12_weeks_from_today" in email_template_context
    assert email_template_context["case"] == case
    assert email_template_context["retest"] is None


@pytest.mark.django_db
def test_get_email_template_context_12_weeks_from_today():
    """Test get_email_template_context 12_weeks_from_today present and correct"""
    with patch(
        "accessibility_monitoring_platform.apps.common.email_template_utils.date"
    ) as mock_date:
        mock_date.today.return_value = date(2023, 2, 1)
        case: Case = Case.objects.create()
        email_template_context: dict[str, Any] = get_email_template_context(case=case)

        assert "12_weeks_from_today" in email_template_context
        assert email_template_context["12_weeks_from_today"] == date(2023, 4, 26)


@pytest.mark.django_db
def test_get_email_template_context_with_audit():
    """Test get_email_template_context for Case with test"""
    case: Case = Case.objects.create()
    Audit.objects.create(case=case)
    email_template_context: dict[str, Any] = get_email_template_context(case=case)

    assert email_template_context["case"] == case
    assert email_template_context["retest"] is None

    assert "issues_tables" in email_template_context
    assert "retest_issues_tables" in email_template_context


@pytest.mark.django_db
def test_get_email_template_context_with_retest():
    """Test get_email_template_context for Case with equality body retest"""
    case: Case = Case.objects.create()
    retest: Retest = Retest.objects.create(case=case)
    email_template_context: dict[str, Any] = get_email_template_context(case=case)

    assert email_template_context["case"] == case
    assert email_template_context["retest"] == retest
