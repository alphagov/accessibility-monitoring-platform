"""
Tests for common models
"""

from ..models import IssueReport


def test_issue_number_incremented_on_creation(admin_user):
    """Test that each new issue_report gets the next issue_report_number"""
    issue_report_one: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_one.issue_number == 1

    issue_report_two: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_two.issue_number == 2
