"""
Test - reports admin actions
"""
import csv
import io

from django.http import HttpResponse
from django.urls import reverse

from ..models import BaseTemplate

BASE_TEMPLATE_NAME_1: str = "Base template name One"
BASE_TEMPLATE_CONTENT_1: str = "Base template content One"
BASE_TEMPLATE_NAME_2: str = "Base template name Two"
BASE_TEMPLATE_CONTENT_2: str = "Base template content Two"


def test_base_template_export_as_csv(admin_client):
    """Test action to export base template as csv"""
    base_template_1: BaseTemplate = BaseTemplate.objects.create(
        name=BASE_TEMPLATE_NAME_1, content=BASE_TEMPLATE_CONTENT_1, position=1
    )
    base_template_2: BaseTemplate = BaseTemplate.objects.create(
        name=BASE_TEMPLATE_NAME_2, content=BASE_TEMPLATE_CONTENT_2, position=2
    )

    response: HttpResponse = admin_client.post(
        reverse("admin:reports_basetemplate_changelist"),
        {
            "action": "export_as_csv",
            "_selected_action": [base_template_1.id, base_template_2.id],
        },
    )

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    cvs_reader = csv.reader(io.StringIO(content))
    rows = list(cvs_reader)

    assert len(rows) == 3
    assert rows[0] == [
        "id",
        "version",
        "created",
        "name",
        "template_type",
        "content",
        "position",
        "new_page",
    ]
    assert rows[1][3] == BASE_TEMPLATE_NAME_1
    assert rows[1][5] == BASE_TEMPLATE_CONTENT_1
    assert rows[2][3] == BASE_TEMPLATE_NAME_2
    assert rows[2][5] == BASE_TEMPLATE_CONTENT_2
