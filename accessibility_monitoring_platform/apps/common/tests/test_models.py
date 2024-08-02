"""
Tests for common models
"""

from ..models import EmailTemplate, IssueReport


def test_issue_number_incremented_on_creation(admin_user):
    """Test that each new issue_report gets the next issue_report_number"""
    issue_report_one: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_one.issue_number == 1

    issue_report_two: IssueReport = IssueReport.objects.create(created_by=admin_user)

    assert issue_report_two.issue_number == 2


def test_email_template_render():
    """Test that email template rendering works"""
    email_template: EmailTemplate = EmailTemplate(
        template="Value from context: {{ context_value }}"
    )

    assert (
        email_template.render(context={"context_value": "value from context"})
        == "Value from context: value from context"
    )
