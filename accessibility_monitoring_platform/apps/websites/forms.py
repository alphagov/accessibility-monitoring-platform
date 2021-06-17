"""
Forms for websites app
"""

from typing import List, Tuple

from django import forms

from ..common.forms import (
    AMPCharField,
    AMPChoiceField,
    AMPDateWidget,
    AMPDateRangeForm,
    AMPModelChoiceField,
)
from .models import Sector

DEFAULT_SORT: str = "-website_id"
SORT_CHOICES: List[Tuple[str, str]] = (
    (DEFAULT_SORT, "Most recently created"),
    # ("error_count", "Fewest Errors"),
    # ("-error_count", "Most Errors"),
    ("-last_updated", "Most recently updated"),
    ("last_updated", "First updated"),
)


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
    sort_by = AMPChoiceField(choices=SORT_CHOICES)
