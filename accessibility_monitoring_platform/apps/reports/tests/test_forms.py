"""
Test forms of reports app
"""
import pytest

from ...cases.models import Case

from ..forms import ReportFeedbackForm
from ..models import Report


@pytest.mark.django_db
def test_report_feedback_is_valid():
    """Tests report feeback form is valid"""
    form: ReportFeedbackForm = ReportFeedbackForm(
        data={
            "what_were_you_trying_to_do": "text",
            "what_went_wrong": "text",
        }
    )
    assert form.is_valid()
