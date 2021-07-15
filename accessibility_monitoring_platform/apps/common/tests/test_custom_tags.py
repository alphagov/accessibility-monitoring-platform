"""
Tests of custom template tags.
"""
import pytest

from ..templatetags.custom_tags import nullable_boolean_label


@pytest.mark.parametrize(
    "value, expected_label",
    [
        (True, "Yes"),
        (False, "No"),
        (None, "Not known"),
    ],
)
def test_nullable_boolean_label_template_filter(value, expected_label):
    """Test nullable_boolean_label returns the correct label for each value"""
    assert nullable_boolean_label(value) == expected_label
