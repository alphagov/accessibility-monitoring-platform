"""
Test templatetags of common app
"""
import pytest

from ..templatetags.common_tags import list_item_by_index


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
