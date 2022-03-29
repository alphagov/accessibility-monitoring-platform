"""
Test utility functions of reports app
"""
import pytest
from typing import List
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.template import Context, Template

from ...audits.models import Audit
from ...cases.models import Case

from ..models import Report, Section, TableRow, BaseTemplate
from ..utils import (
    check_for_buttons_by_name,
    delete_table_row,
    move_table_row_down,
    move_table_row_up,
    generate_report_content,
    undelete_table_row,
    DELETE_ROW_BUTTON_PREFIX,
    UNDELETE_ROW_BUTTON_PREFIX,
    MOVE_ROW_UP_BUTTON_PREFIX,
    MOVE_ROW_DOWN_BUTTON_PREFIX,
)

NUMBER_OF_BASE_TEMPLATES: int = 9
PREVIOUS_ROW_POSITION: int = 1
ORIGINAL_ROW_POSITION: int = 2
NEXT_ROW_POSITION: int = 3


def create_table_row() -> TableRow:
    """Create a table row"""
    case: Case = Case.objects.create()
    report: Report = Report.objects.create(case=case)
    section: Section = Section.objects.create(report=report, position=1)
    return TableRow.objects.create(section=section, row_number=1)


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


@pytest.mark.django_db
def test_delete_table_row(rf):
    """Test delete_table_row marks table row as deleted"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    request: HttpRequest = rf.post("/", {f"{DELETE_ROW_BUTTON_PREFIX}{table_row_id}": "Button"})
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@…", password="secret"
    )
    request.user = user

    assert not table_row.is_deleted

    delete_table_row(request=request)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    assert updated_table_row.is_deleted


@pytest.mark.django_db
def test_undelete_table_row(rf):
    """Test undelete_table_row marks table row as not deleted"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    request: HttpRequest = rf.post("/", {f"{UNDELETE_ROW_BUTTON_PREFIX}{table_row_id}": "Button"})
    user: User = User.objects.create_user(  # type: ignore
        username="mockuser", email="mockuser@…", password="secret"
    )
    request.user = user

    table_row.is_deleted = True
    table_row.save()

    undelete_table_row(request=request)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    assert not updated_table_row.is_deleted


@pytest.mark.django_db
def test_move_table_row_up(rf):
    """Test move_table_row_up swaps table row's position with the previous"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    table_row.row_number = ORIGINAL_ROW_POSITION
    table_row.save()
    previous_row: TableRow = TableRow.objects.create(
        section=table_row.section, row_number=PREVIOUS_ROW_POSITION
    )

    request: HttpRequest = rf.post("/", {f"{MOVE_ROW_UP_BUTTON_PREFIX}{table_row_id}": "Button"})

    move_table_row_up(request=request, section=table_row.section)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    updated_previous_row: TableRow = TableRow.objects.get(id=previous_row.id)  # type: ignore

    assert updated_table_row.row_number == PREVIOUS_ROW_POSITION
    assert updated_previous_row.row_number == ORIGINAL_ROW_POSITION


@pytest.mark.django_db
def test_move_table_row_down(rf):
    """Test move_table_row_down swaps table row's position with the next"""
    table_row: TableRow = create_table_row()
    table_row_id: int = table_row.id  # type: ignore
    table_row.row_number = ORIGINAL_ROW_POSITION
    table_row.save()
    next_row: TableRow = TableRow.objects.create(
        section=table_row.section, row_number=NEXT_ROW_POSITION
    )

    request: HttpRequest = rf.post("/", {f"{MOVE_ROW_DOWN_BUTTON_PREFIX}{table_row_id}": "Button"})

    move_table_row_down(request=request, section=table_row.section)

    updated_table_row: TableRow = TableRow.objects.get(id=table_row_id)
    updated_next_row: TableRow = TableRow.objects.get(id=next_row.id)  # type: ignore

    assert updated_table_row.row_number == NEXT_ROW_POSITION
    assert updated_next_row.row_number == ORIGINAL_ROW_POSITION
