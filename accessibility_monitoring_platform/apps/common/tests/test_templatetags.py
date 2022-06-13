"""
Test templatetags of common app
"""
from datetime import date, datetime
import pytest

from ..templatetags.common_tags import (
    gds_date,
    gds_datetime,
    gds_time,
    list_item_by_index,
    markdown_to_html,
)


@pytest.mark.parametrize(
    "item_list,index,expected_result",
    [
        (["a", "b", "c"], 1, "b"),
        ([], 1, None),
        (None, None, None),
    ],
)
def test_list_item_by_index(item_list, index, expected_result):
    """Test that templatetag returns indexed item from list or none"""
    assert list_item_by_index(item_list, index) == expected_result


def test_markdown_to_html():
    """Test markdown converted to HTML."""
    assert markdown_to_html("# Heading") == "<h1>Heading</h1>"


def test_markdown_to_html_escapes_html():
    """Test markdown converted to HTML escapes any included HTML."""
    assert (
        markdown_to_html("<script>Bad stuff</script>")
        == "<p>&lt;script&gt;Bad stuff&lt;/script&gt;</p>"
    )


@pytest.mark.parametrize(
    "date_to_format,expected_result",
    [
        (date(2021, 4, 1), "1 April 2021"),
        (None, ""),
    ],
)
def test_gds_date(date_to_format, expected_result):
    """Test date formatted according to GDS style guide."""
    assert gds_date(date_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 4, 1, 9, 1), "9:01am"),
        (None, ""),
    ],
)
def test_gds_time(datetime_to_format, expected_result):
    """Test time formatted according to GDS style guide."""
    assert gds_time(datetime_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 4, 1, 9, 1), "1 April 2021 9:01am"),
        (None, ""),
    ],
)
def test_gds_datetime(datetime_to_format, expected_result):
    """Test date and time formatted according to GDS style guide."""
    assert gds_datetime(datetime_to_format) == expected_result
