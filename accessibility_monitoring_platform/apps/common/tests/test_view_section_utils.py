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
    assert build_view_section(
        name=SECTION_NAME, edit_url=EDIT_URL, edit_url_id=EDIT_URL_ID
    ) == ViewSection(
        name=SECTION_NAME,
        anchor="section-name",
        edit_url=EDIT_URL,
        edit_url_id=EDIT_URL_ID,
        complete=False,
        display_fields=None,
        subtables=None,
        subsections=None,
    )

    assert build_view_section(
        name=SECTION_NAME,
        edit_url=EDIT_URL,
        edit_url_id=EDIT_URL_ID,
        complete_date=COMPLETE_DATE,
        anchor=ANCHOR,
        display_fields=["fields"],
        subtables=["subtable"],
        subsections=["subsection"],
    ) == ViewSection(
        name=SECTION_NAME,
        anchor=ANCHOR,
        edit_url=EDIT_URL,
        edit_url_id=EDIT_URL_ID,
        complete=True,
        display_fields=["fields"],
        subtables=["subtable"],
        subsections=["subsection"],
    )
