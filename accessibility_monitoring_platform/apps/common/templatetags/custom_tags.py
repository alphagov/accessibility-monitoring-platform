"""
Custom template filters
"""
from typing import Dict, Union

from django import template

from ..forms import BOOLEAN_CHOICES

nullable_boolean_labels: Dict[Union[bool, None], str] = {
    value: label for value, label in BOOLEAN_CHOICES
}

register = template.Library()


@register.filter
def nullable_boolean_label(value):
    """Convert nullable boolean value into its label"""
    return nullable_boolean_labels.get(value, "")
