"""
Forms - cases
"""
from datetime import datetime
import pytz

from django import forms
from django.core.exceptions import ValidationError

from .models import STATUS_CHOICES

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


def convert_day_month_year_to_date(day: str, month: str, year: str) -> datetime:
    """ Convert given day, month and year to a datetime """
    return datetime(year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC)


class SearchForm(forms.Form):
    """
    Form for searching for cases
    """

    sort_by = forms.ChoiceField(
        label="Sort by",
        widget=forms.Select(attrs={"class": "govuk-select"}),
        required=False,
        choices=SORT_CHOICES,
    )

    case_number = forms.CharField(
        label="Case number",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        required=False,
    )

    domain = forms.CharField(
        label="Domain",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        required=False,
    )

    organisation = forms.CharField(
        label="Organisation",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        required=False,
    )

    auditor = forms.ChoiceField(
        label="Auditor",
        widget=forms.Select(attrs={"class": "govuk-select"}),
        required=False,
        choices=AUDITOR_CHOICES,
    )

    status = forms.ChoiceField(
        label="Status",
        widget=forms.Select(attrs={"class": "govuk-select"}),
        required=False,
        choices=status_choices,
    )

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

    def clean_start_date_year(self):
        start_date_day_clean: str = self.cleaned_data.get("start_date_day")
        start_date_month_clean: str = self.cleaned_data.get("start_date_month")
        start_date_year_clean: str = self.cleaned_data.get("start_date_year")
        if (
            start_date_day_clean is not None
            or start_date_month_clean is not None
            or start_date_year_clean is not None
        ):
            try:
                datetime(
                    day=int(start_date_day_clean),
                    month=int(start_date_month_clean),
                    year=int(start_date_year_clean),
                )
            except Exception as e:
                raise ValidationError(
                    "This date is invalid",
                    code="email_is_not_permitted",
                ) from e
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

    def clean_end_date_year(self):
        end_date_day_clean: str = self.cleaned_data.get("end_date_day")
        end_date_month_clean: str = self.cleaned_data.get("end_date_month")
        end_date_year_clean: str = self.cleaned_data.get("end_date_year")
        if (
            end_date_day_clean is not None
            or end_date_month_clean is not None
            or end_date_year_clean is not None
        ):
            try:
                datetime(
                    day=int(end_date_day_clean),
                    month=int(end_date_month_clean),
                    year=int(end_date_year_clean),
                )
            except Exception as e:
                raise ValidationError(
                    "This date is invalid",
                    code="email_is_not_permitted",
                ) from e
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
