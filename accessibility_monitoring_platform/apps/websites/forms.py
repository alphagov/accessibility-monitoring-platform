"""
Forms for websites app
"""

from django import forms

from ..common.forms import (
    AMPCharField,
    AMPDateWidget,
    AMPDateRangeForm,
    AMPModelChoiceField,
)
from .models import Sector


class WebsiteSearchForm(AMPDateRangeForm):
    """
    Form for filtering websites
    """

    service = AMPCharField(label="Service")
    sector = AMPModelChoiceField(
        label="Sector",
        queryset=Sector.objects.using("pubsecweb_db").all().order_by("sector_name"),
    )
    location = AMPCharField(label="Town/City")
    start_date = forms.DateField(
        label="Last Updated Start date", widget=AMPDateWidget(), required=False
    )
    end_date = forms.DateField(
        label="Last Updated End date", widget=AMPDateWidget(), required=False
    )
