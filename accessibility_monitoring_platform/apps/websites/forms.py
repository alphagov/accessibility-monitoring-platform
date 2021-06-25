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
    # Todo: Add axe error count columns
    # ("error_count", "Fewest errors"),
    # ("-error_count", "Most errors"),
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
    location = AMPCharField(label="Town/city")
    start_date = forms.DateField(
        label="Last updated start date", widget=AMPDateWidget(), required=False
    )
    end_date = forms.DateField(
        label="Last updated end date", widget=AMPDateWidget(), required=False
    )
    sort_by = AMPChoiceField(choices=SORT_CHOICES)
