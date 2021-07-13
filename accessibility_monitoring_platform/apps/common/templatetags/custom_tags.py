"""
Custom template filters
"""

from django import template

from ..forms import NULLABLE_BOOLEAN_CHOICES

nullable_boolean_labels = {value: label for value, label in NULLABLE_BOOLEAN_CHOICES}

register = template.Library()


@register.filter
def nullable_boolean_label(value):
    """ Convert nullable boolean value into its label """
    return nullable_boolean_labels.get(value, "")
