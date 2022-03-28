"""
Test utility functions of reports app
"""
import pytest
from typing import List
from unittest.mock import patch

from django.http import HttpRequest
from django.template import Context, Template

from ...audits.models import Audit
from ...cases.models import Case

from ..models import Report, Section, BaseTemplate
from ..utils import (
    check_for_buttons_by_name,
    generate_report_content,
)

NUMBER_OF_BASE_TEMPLATES: int = 9


@pytest.mark.django_db
def test_generate_report_content():
    """Test new reports use BaseTemplates to create their sections"""
    base_templates: List[BaseTemplate] = list(BaseTemplate.objects.all())
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    context: Context = Context({"audit": audit})
    report: Report = Report.objects.create(case=case)

    generate_report_content(report=report)

    sections: List[Section] = list(report.section_set.all())  # type: ignore

    assert len(base_templates) == NUMBER_OF_BASE_TEMPLATES
    assert len(sections) == NUMBER_OF_BASE_TEMPLATES

    for section, base_template in zip(sections, base_templates):
        assert section.name == base_template.name
        assert section.template_type == base_template.template_type
        assert section.position == base_template.position

        template: Template = Template(base_template.content)
        assert section.content == template.render(context=context)


@pytest.mark.parametrize(
    "first_return, second_return, third_return, fourth_return, overall_return",
    [
        (None, None, None, None, None),
        (1, None, None, None, 1),
        (None, 2, None, None, 2),
        (None, None, 3, None, 3),
        (None, None, None, 4, 4),
    ],
)
def test_check_for_buttons_by_name(
    first_return, second_return, third_return, fourth_return, overall_return
):
    """
    Test check_for_buttons_by_name calls functions until an id is returned and then
    returns that id.
    """
    mock_request: HttpRequest = HttpRequest()
    mock_section: Section = Section()
    with patch(
        "accessibility_monitoring_platform.apps.reports.utils.delete_table_row",
        return_value=first_return,
    ) as mock_delete_table_row, patch(
        "accessibility_monitoring_platform.apps.reports.utils.undelete_table_row",
        return_value=second_return,
    ) as mock_undelete_table_row, patch(
        "accessibility_monitoring_platform.apps.reports.utils.move_table_row_up",
        return_value=third_return,
    ) as mock_move_table_row_up, patch(
        "accessibility_monitoring_platform.apps.reports.utils.move_table_row_down",
        return_value=fourth_return,
    ) as mock_move_table_row_down:
        assert check_for_buttons_by_name(mock_request, mock_section) == overall_return

    mock_delete_table_row.assert_called_once()

    if first_return is None:
        mock_undelete_table_row.assert_called_once()
        if second_return is None:
            mock_move_table_row_up.assert_called_once()
            if third_return is None:
                mock_move_table_row_down.assert_called_once()
            else:
                mock_move_table_row_down.assert_not_called()
        else:
            mock_move_table_row_up.assert_not_called()
            mock_move_table_row_down.assert_not_called()
    else:
        mock_undelete_table_row.assert_not_called()
        mock_move_table_row_up.assert_not_called()
        mock_move_table_row_down.assert_not_called()
