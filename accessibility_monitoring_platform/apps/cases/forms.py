"""
Forms - cases
"""
from datetime import datetime
import pytz
from typing import Tuple, Union

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Case,
    Contact,
    CASE_ORIGIN_CHOICES,
    STATUS_CHOICES,
    TEST_TYPE_CHOICES,
    WEBSITE_TYPE_CHOICES,
)

DEFAULT_START_DATE = datetime(year=1900, month=1, day=1, tzinfo=pytz.UTC)
DEFAULT_END_DATE = datetime(year=2100, month=1, day=1, tzinfo=pytz.UTC)

AUDITOR_CHOICES = [
    ("", ""),
    ("Andrew Hick", "Andrew Hick"),
    ("Jessica Eley", "Jessica Eley"),
    ("Katherine Badger", "Katherine Badger"),
    ("Kelly Clarkson", "Kelly Clarkson"),
    ("Keeley Robertson", "Keeley Robertson"),
    ("Nesha Russo", "Nesha Russo"),
]

status_choices = STATUS_CHOICES
status_choices.insert(0, ("", "All"))

SORT_CHOICES = [
    ("-id", "Newest"),
    ("id", "Oldest"),
]

StringOrNone = Union[str, None]


from django.template import loader
from django.utils.safestring import mark_safe


class AMPRadioSelectWidget(forms.RadioSelect):
    template_name = "cases/amp_radio_select_widget_template.html"


class AMPCheckboxWidget(forms.CheckboxInput):
    template_name = "cases/amp_checkbox_widget_template.html"


def check_date_valid_or_none(
    day: StringOrNone, month: StringOrNone, year: StringOrNone
) -> None:
    """ Check if given day, month and year are all none or make a valid date """
    if year is not None or month is not None or day is not None:
        try:
            datetime(day=int(day), month=int(month), year=int(year))
        except Exception as e:
            raise ValidationError("This date is invalid", code="invalid_date") from e


def convert_day_month_year_to_date(day: str, month: str, year: str) -> datetime:
    """ Convert given day, month and year to a datetime """
    return datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)


class AMPCharField(forms.CharField):
    """ Adds default max_length and widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "max_length": 100,
            "widget": forms.TextInput(
                attrs={"class": "govuk-input govuk-input--width-10"}
            ),
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPCharFieldWide(forms.CharField):
    """ Adds default widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.TextInput(attrs={"class": "govuk-input"}),
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPChoiceField(forms.ChoiceField):
    """ Adds default widget to Django forms ChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.Select(attrs={"class": "govuk-select"}),
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPBooleanField(forms.BooleanField):
    """ Adds default widget to Django forms BooleanField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.CheckboxInput(attrs={"class": "govuk-checkboxes__input"}),
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class DateRangeForm(forms.Form):
    """
    Form used to filter by date range.
    Start and end dates default to span entire period.
    """

    start_date_day = forms.IntegerField(
        label="Start Date",
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-2",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    start_date_month = forms.IntegerField(
        label="Start Date",
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-2",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    start_date_year = forms.IntegerField(
        label="Start Date",
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-4",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    def clean_start_date_year(self) -> str:
        """ Check day, month and year values make a valid date """
        start_date_day_clean: str = self.cleaned_data.get("start_date_day")
        start_date_month_clean: str = self.cleaned_data.get("start_date_month")
        start_date_year_clean: str = self.cleaned_data.get("start_date_year")
        check_date_valid_or_none(
            start_date_day_clean, start_date_month_clean, start_date_year_clean
        )
        return self.cleaned_data.get("start_date_year")

    end_date_day = forms.IntegerField(
        label="End Date",
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-2",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    end_date_month = forms.IntegerField(
        label="End Date",
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-2",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    end_date_year = forms.IntegerField(
        label="End Date",
        widget=forms.NumberInput(
            attrs={
                "class": "govuk-input govuk-date-input__input govuk-input--width-4",
                "type": "number",
                "pattern": "[0-9]*",
                "inputmode": "numeric",
            }
        ),
        required=False,
    )

    def clean_end_date_year(self) -> str:
        """ Check day, month and year values make a valid date """
        end_date_day_clean: str = self.cleaned_data.get("end_date_day")
        end_date_month_clean: str = self.cleaned_data.get("end_date_month")
        end_date_year_clean: str = self.cleaned_data.get("end_date_year")
        check_date_valid_or_none(
            end_date_day_clean, end_date_month_clean, end_date_year_clean
        )
        return self.cleaned_data.get("end_date_year")

    @property
    def start_date(self) -> datetime:
        """
        Build start_date timestamp from entered day, month and year.
        Return default start_date if no valid date was entered.
        """
        try:
            day: str = self.cleaned_data.get("start_date_day")
            month: str = self.cleaned_data.get("start_date_month")
            year: str = self.cleaned_data.get("start_date_year")
            return convert_day_month_year_to_date(day, month, year)
        except (ValueError, TypeError):
            return DEFAULT_START_DATE

    @property
    def end_date(self) -> datetime:
        """
        Build end_date timestamp from entered day, month and year.
        Return default end_date if not valid date was entered.
        """
        try:
            day: str = self.cleaned_data.get("end_date_day")
            month: str = self.cleaned_data.get("end_date_month")
            year: str = self.cleaned_data.get("end_date_year")
            return convert_day_month_year_to_date(day, month, year)
        except (ValueError, TypeError):
            return DEFAULT_END_DATE


class SearchForm(DateRangeForm):
    """
    Form for searching for cases
    """

    sort_by = AMPChoiceField(label="Sort by", choices=SORT_CHOICES)
    case_number = AMPCharField(label="Case number", required=False)
    domain = AMPCharField(label="Domain", required=False)
    organisation = AMPCharField(label="Organisation", required=False)
    auditor = AMPChoiceField(label="Auditor", choices=AUDITOR_CHOICES, required=False)
    status = AMPChoiceField(label="Status", choices=status_choices, required=False)


class CaseWebsiteDetailUpdateForm(forms.ModelForm):
    """
    Form for updating website details fields of cases
    """

    auditor = AMPCharFieldWide(label="Auditor", required=False)
    test_type = AMPChoiceField(
        label="Test type",
        choices=TEST_TYPE_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    home_page_url = AMPCharFieldWide(
        label="Full URL",
        required=False,
        help_text="Enter a domain if test type is simple or complex",
    )
    organisation_name = AMPCharFieldWide(label="Organisation name", required=False)
    website_type = AMPChoiceField(
        label="Type of site",
        choices=WEBSITE_TYPE_CHOICES,
        required=False,
        widget=AMPRadioSelectWidget,
    )
    sector = AMPCharFieldWide(label="Sector", required=False)
    region = AMPCharFieldWide(label="Region", required=False)
    case_origin = AMPChoiceField(
        label="Case origin", choices=CASE_ORIGIN_CHOICES, widget=AMPRadioSelectWidget
    )
    zendesk_url = AMPCharFieldWide(label="Zendesk ticket URL", required=False)
    trello_url = AMPCharFieldWide(label="Trello ticket URL", required=False)
    notes = AMPCharFieldWide(label="Notes", required=False)
    is_public_sector_body = AMPBooleanField(
        label="Public sector body?",
        help_text="If you later find out the organisation is not a public sector body, unmark the checkbox, then save and exit to unlist the case.",
        widget=AMPCheckboxWidget(
            attrs={
                "label": "Untick this box to unlist the case",
            }
        ),
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            "auditor",
            "test_type",
            "home_page_url",
            "organisation_name",
            "website_type",
            "sector",
            "region",
            "case_origin",
            "zendesk_url",
            "trello_url",
            "notes",
            "is_public_sector_body",
        ]


class ContactUpdateForm(forms.ModelForm):
    """
    Form for updating a contact
    """

    first_name = AMPCharFieldWide(label="First name", required=False)
    last_name = AMPCharFieldWide(label="Last name", required=False)
    job_title = AMPCharFieldWide(label="Job title", required=False)
    detail = AMPCharFieldWide(label="Detail", required=False)
    preferred = AMPBooleanField(
        label="Preferred contact?", widget=AMPCheckboxWidget(), required=False
    )
    notes = AMPCharFieldWide(label="Notes", required=False)

    class Meta:
        model = Case
        fields = [
            "first_name",
            "last_name",
            "job_title",
            "detail",
            "preferred",
            "notes",
        ]
