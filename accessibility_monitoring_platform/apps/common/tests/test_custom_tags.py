"""
Tests of custom template tags.
"""
import pytest

from ..templatetags.custom_tags import boolean_label


@pytest.mark.parametrize(
    "value, expected_label",
    [
        (True, "Yes"),
        (False, "No"),
        (None, "Not known"),
    ],
)
def test_boolean_label_template_filter(value, expected_label):
    """Test boolean_label returns the correct label for each value"""
    assert boolean_label(value) == expected_label
