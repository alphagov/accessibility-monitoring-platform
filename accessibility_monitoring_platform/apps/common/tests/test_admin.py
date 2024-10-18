"""
Test - common admin actions
"""

import csv
import io

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

from ..models import IssueReport

ISSUE_REPORT_DESCRIPTION_1: str = "Issue One"
ISSUE_REPORT_DESCRIPTION_2: str = "Issue Two"


def test_issue_report_export_as_csv(admin_client):
    """Test action to export issue reports as csv"""
    user: User = User.objects.create()
    issue_report_1: IssueReport = IssueReport.objects.create(
        created_by=user, description=ISSUE_REPORT_DESCRIPTION_1
    )
    issue_report_2: IssueReport = IssueReport.objects.create(
        created_by=user, description=ISSUE_REPORT_DESCRIPTION_2
    )

    response: HttpResponse = admin_client.post(
        reverse("admin:common_issuereport_changelist"),
        {
            "action": "export_as_csv",
            "_selected_action": [issue_report_1.id, issue_report_2.id],
        },
    )

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    csv_reader = csv.reader(io.StringIO(content))
    rows = list(csv_reader)

    assert len(rows) == 3
    assert rows[0] == [
        "id",
        "issue_number",
        "page_url",
        "page_title",
        "description",
        "created_by",
        "created",
        "complete",
        "trello_ticket",
        "notes",
    ]
    assert rows[1][4] == ISSUE_REPORT_DESCRIPTION_2
    assert rows[2][4] == ISSUE_REPORT_DESCRIPTION_1
