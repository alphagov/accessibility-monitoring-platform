"""
Test - common utility function to extract labels and values from forms
"""

from datetime import date

from ..view_section_utils import ViewSection, build_view_section

SECTION_NAME: str = "Section name"
EDIT_URL: str = "/url/path"
EDIT_URL_ID: str = "url-id"
COMPLETE_DATE: date = date(2024, 2, 29)
ANCHOR: str = "anchor"


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
    assert view_section.type == ViewSection.FORM_TYPE
    assert view_section.page is None
    assert view_section.statement_check_results is None

    view_section: ViewSection = build_view_section(
        name=SECTION_NAME,
        edit_url=EDIT_URL,
        edit_url_id=EDIT_URL_ID,
        complete_date=COMPLETE_DATE,
        anchor=ANCHOR,
        display_fields=["fields"],
        subtables=["subtable"],
        subsections=["subsection"],
        type=ViewSection.INITIAL_STATEMENT_RESULTS,
        page="Page",
        statement_check_results=["statement_check_result"],
    )

    assert view_section.name == SECTION_NAME
    assert view_section.anchor == ANCHOR
    assert view_section.edit_url == EDIT_URL
    assert view_section.edit_url_id == EDIT_URL_ID
    assert view_section.complete is True
    assert view_section.display_fields == ["fields"]
    assert view_section.subtables == ["subtable"]
    assert view_section.subsections == ["subsection"]
    assert view_section.type == ViewSection.INITIAL_STATEMENT_RESULTS
    assert view_section.page == "Page"
    assert view_section.statement_check_results == ["statement_check_result"]
