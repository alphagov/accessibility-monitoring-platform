"""
Test templatetags of common app
"""

from datetime import date, datetime, timezone

import pytest

from ..templatetags.common_tags import (
    amp_date,
    amp_date_trunc,
    amp_datetime,
    amp_datetime_short_month,
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


def test_markdown_to_html_undoes_double_escapes_html():
    """Test markdown converted to HTML undoes any double escapes."""
    assert (
        markdown_to_html("`<span>span in code</code>`\n\n&lt;")
        == "<p><code>&lt;span&gt;span in code&lt;/code&gt;</code></p>\n<p>&lt;</p>"
    )


@pytest.mark.parametrize(
    "date_to_format,expected_result",
    [
        (date(2021, 4, 1), "1 April 2021"),
        (None, ""),
    ],
)
def test_amp_date(date_to_format, expected_result):
    """Test date formatted according to GDS style guide."""
    assert amp_date(date_to_format) == expected_result


@pytest.mark.parametrize(
    "date_to_format,expected_result",
    [
        (date(2021, 4, 1), "1 Apr 21"),
        (None, ""),
    ],
)
def test_amp_date_trunc(date_to_format, expected_result):
    """Test date formatted according to GDS style guide."""
    assert amp_date_trunc(date_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 1, 4, 9, 1, 0, 0, timezone.utc), "4 January 2021 9:01am"),
        (datetime(2021, 7, 4, 8, 1, 0, 0, timezone.utc), "4 July 2021 9:01am"),
        (None, ""),
    ],
)
def test_amp_datetime(datetime_to_format, expected_result):
    """Test date and time formatted according to GDS style guide."""
    assert amp_datetime(datetime_to_format) == expected_result


@pytest.mark.parametrize(
    "datetime_to_format,expected_result",
    [
        (datetime(2021, 1, 4, 9, 1, 0, 0, timezone.utc), "4 Jan 21 9:01am"),
        (datetime(2021, 7, 4, 8, 1, 0, 0, timezone.utc), "4 Jul 21 9:01am"),
        (None, ""),
    ],
)
def test_amp_datetime_short_month(datetime_to_format, expected_result):
    """Test date and time formatted according to GDS style guide."""
    assert amp_datetime_short_month(datetime_to_format) == expected_result
