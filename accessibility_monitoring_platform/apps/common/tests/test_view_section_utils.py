"""
Test - common utility function to extract labels and values from forms
"""

from datetime import date
from typing import List

import pytest

from ..view_section_utils import (
    ViewSection,
    add_content_ids_for_accordion,
    build_view_section,
)

SECTION_NAME: str = "Section name"
EDIT_URL: str = "/url/path"
EDIT_URL_ID: str = "url-id"
COMPLETE_DATE: date = date(2024, 2, 29)
ANCHOR: str = "anchor"
PLACEHOLDER: str = "No data to display"


@pytest.mark.parametrize(
    "type",
    [ViewSection.Type.INITIAL_WCAG_RESULTS, ViewSection.Type.TWELVE_WEEK_WCAG_RESULTS],
)
def test_view_section_raises_missing_page_exception(type):
    """Test ViewSection raises missing page exception."""

    with pytest.raises(ValueError, match="Page missing from WCAG results section."):
        ViewSection(name=SECTION_NAME, type=type)

    ViewSection(name=SECTION_NAME, type=type, page="page")


@pytest.mark.parametrize(
    "type",
    [
        ViewSection.Type.INITIAL_STATEMENT_RESULTS,
        ViewSection.Type.TWELVE_WEEK_STATEMENT_RESULTS,
    ],
)
def test_view_section_raises_missing_statement_results_exception(type):
    """Test ViewSection raises missing statement results exception."""

    with pytest.raises(
        ValueError, match="Results missing from statement results section."
    ):
        ViewSection(name=SECTION_NAME, type=type)

    ViewSection(
        name=SECTION_NAME, type=type, statement_check_results=["statement check result"]
    )


def test_has_content_no_content():
    """Test ViewSection has no content"""
    view_section = ViewSection(name=SECTION_NAME)

    assert view_section.has_content is False


def test_has_content_no_contenti_empty_lists():
    """
    Test ViewSection has no content when lists are empty
    instead of None.
    """
    view_section = ViewSection(
        name=SECTION_NAME, display_fields=[], subtables=[], subsections=[]
    )

    assert view_section.has_content is False


@pytest.mark.parametrize(
    "attr",
    ["display_fields", "subtables", "subsections", "page", "statement_check_results"],
)
def test_has_content(attr: str):
    """Test ViewSection has content"""
    view_section = ViewSection(name=SECTION_NAME)
    setattr(view_section, attr, "content")

    assert view_section.has_content is True


def test_build_view_section():
    """
    Test building of view section object for use in view context
    """
    view_section: ViewSection = build_view_section(
        name=SECTION_NAME, edit_url=EDIT_URL, edit_url_id=EDIT_URL_ID
    )

    assert view_section.name == SECTION_NAME
    assert view_section.anchor == "section-name"
    assert view_section.edit_url == EDIT_URL
    assert view_section.edit_url_id == EDIT_URL_ID
    assert view_section.complete is False
    assert view_section.display_fields is None
    assert view_section.subtables is None
    assert view_section.subsections is None
    assert view_section.type == ViewSection.Type.FORM_TYPE
    assert view_section.page is None
    assert view_section.statement_check_results is None

    view_section: ViewSection = build_view_section(
        name=SECTION_NAME,
        edit_url=EDIT_URL,
        edit_url_id=EDIT_URL_ID,
        complete_date=COMPLETE_DATE,
        anchor=ANCHOR,
        placeholder=PLACEHOLDER,
        display_fields=["fields"],
        subtables=["subtable"],
        subsections=["subsection"],
        type=ViewSection.Type.INITIAL_STATEMENT_RESULTS,
        page="Page",
        statement_check_results=["statement_check_result"],
    )

    assert view_section.name == SECTION_NAME
    assert view_section.anchor == ANCHOR
    assert view_section.placeholder == PLACEHOLDER
    assert view_section.edit_url == EDIT_URL
    assert view_section.edit_url_id == EDIT_URL_ID
    assert view_section.complete is True
    assert view_section.display_fields == ["fields"]
    assert view_section.subtables == ["subtable"]
    assert view_section.subsections == ["subsection"]
    assert view_section.type == ViewSection.Type.INITIAL_STATEMENT_RESULTS
    assert view_section.page == "Page"
    assert view_section.statement_check_results == ["statement_check_result"]


def test_add_content_ids_for_accordion():
    """
    Test content ids are added to the ViewSections to provide
    expected ids for aria-controls in GDS Design System accordion.
    """
    assert add_content_ids_for_accordion([]) == []

    view_sections: List[ViewSection] = [
        ViewSection(
            name="Name 1",
            anchor="name-1",
        ),
        ViewSection(
            name="Name 2",
            anchor="name-2",
        ),
    ]

    assert [
        view_section.content_id
        for view_section in add_content_ids_for_accordion(view_sections)
    ] == [1, 2]


def test_add_content_ids_for_accordion_subsections():
    """
    Test content ids are added to the ViewSections to provide
    expected ids for aria-controls in GDS Design System accordion.
    Subsections which get their own accordion section elements in the
    UI need incremented ids.
    """
    view_sections: List[ViewSection] = [
        ViewSection(
            name="Name 1",
            anchor="name-1",
            subsections=[
                ViewSection(
                    name="Name 1a",
                    anchor="name-1a",
                )
            ],
        ),
        ViewSection(
            name="Name 2",
            anchor="name-2",
        ),
    ]

    view_sections_with_content_ids: List[ViewSection] = add_content_ids_for_accordion(
        view_sections
    )
    content_ids: List[int] = []
    for view_section in view_sections_with_content_ids:
        content_ids.append(view_section.content_id)
        if view_section.subsections is not None:
            for subsection in view_section.subsections:
                content_ids.append(subsection.content_id)

    assert content_ids == [1, 2, 3]


def test_add_content_ids_for_accordion_subsections_when_parent_has_no_anchor():
    """
    Test content ids are added to the ViewSections to provide
    expected ids for aria-controls in GDS Design System accordion.
    Subsections which get their own accordion section elements in the
    UI need incremented ids even if the parent section has no anchor.
    """
    view_sections: List[ViewSection] = [
        ViewSection(
            name="Name 1",
            anchor="name-1",
        ),
        ViewSection(
            name="Name 2",
            subsections=[
                ViewSection(
                    name="Name 2a",
                    anchor="name-2a",
                )
            ],
        ),
    ]

    view_sections_with_content_ids: List[ViewSection] = add_content_ids_for_accordion(
        view_sections
    )
    content_ids: List[int] = []
    for view_section in view_sections_with_content_ids:
        content_ids.append(view_section.content_id)
        if view_section.subsections is not None:
            for subsection in view_section.subsections:
                content_ids.append(subsection.content_id)

    assert content_ids == [1, 1, 2]


def test_add_content_ids_for_accordion_audit_results():
    """
    Test content ids are added to the ViewSections to provide
    expected ids for aria-controls in GDS Design System accordion.
    Test result subsections do not get their own accordion section
    elements in the UI should not have incremented ids.
    These ids are not used and incrementing them makes subsequent
    ids wrong.
    """
    view_sections: List[ViewSection] = [
        ViewSection(
            name="Name 1",
            anchor="name-1",
            type=ViewSection.Type.AUDIT_RESULTS_ON_VIEW_CASE,
            subsections=[
                ViewSection(
                    name="Name 1a",
                    anchor="name-1a",
                )
            ],
        ),
        ViewSection(
            name="Name 2",
            anchor="name-2",
        ),
    ]

    view_sections_with_content_ids: List[ViewSection] = add_content_ids_for_accordion(
        view_sections
    )
    content_ids: List[int] = []
    for view_section in view_sections_with_content_ids:
        content_ids.append(view_section.content_id)
        if view_section.subsections is not None:
            for subsection in view_section.subsections:
                content_ids.append(subsection.content_id)

    assert content_ids == [1, 1, 2]
