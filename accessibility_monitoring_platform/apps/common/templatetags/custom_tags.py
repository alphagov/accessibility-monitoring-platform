"""
Custom template filters
"""
from typing import Dict, Union

from django import template

from ..forms import NULLABLE_BOOLEAN_CHOICES

boolean_labels: Dict[Union[bool, None], str] = {
    value: label for value, label in NULLABLE_BOOLEAN_CHOICES
}

register = template.Library()


@register.filter
def boolean_label(value):
    """Convert boolean value into its label"""
    return boolean_labels.get(value, "")
