"""
Test templatetags of common app
"""
import pytest

from ..templatetags.common_tags import list_item_by_index, markdown_to_html


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
