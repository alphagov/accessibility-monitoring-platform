"""
Forms for querying Axe test results.
"""
import datetime
import pytz
from django import forms
from django.core.exceptions import ValidationError

DEFAULT_START_DATE = datetime.datetime(year=1900, month=1, day=1, tzinfo=pytz.UTC)
DEFAULT_END_DATE = datetime.datetime(year=2100, month=1, day=1, tzinfo=pytz.UTC)


def check_date_valid_or_none(day, month, year):
    if year is not None or month is not None or day is not None:
        try:
            datetime.datetime(day=int(day), month=int(month), year=int(year))
        except Exception as e:
            raise ValidationError("This date is invalid", code="invalid_date") from e


def convert_day_month_year_to_date(
    day: str, month: str, year: str
) -> datetime.datetime:
    return datetime.datetime(
        year=int(year), month=int(month), day=int(day), tzinfo=pytz.UTC
    )


class AxeDataSearchForm(forms.Form):
    """
    Form used to filter Axe test results.

    Start and end dates default to span entire period.
    """

    domain_name = forms.CharField(
        label="Domain",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        required=False,
    )

    start_date_day = forms.IntegerField(
        label="Tested Start Date",
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
        label="Tested Start Date",
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
        label="Tested Start Date",
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
        check_date_valid_or_none(
            start_date_day_clean, start_date_month_clean, start_date_year_clean
        )
        return self.cleaned_data.get("start_date_year")

    end_date_day = forms.IntegerField(
        label="Tested End Date",
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
        label="Tested End Date",
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
        label="Tested End Date",
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
        check_date_valid_or_none(
            end_date_day_clean, end_date_month_clean, end_date_year_clean
        )
        return self.cleaned_data.get("end_date_year")

    @property
    def start_date(self):
        try:
            day: str = self.cleaned_data.get("start_date_day")
            month: str = self.cleaned_data.get("start_date_month")
            year: str = self.cleaned_data.get("start_date_year")
            return convert_day_month_year_to_date(day, month, year)
        except (ValueError, TypeError):
            return DEFAULT_START_DATE

    @property
    def end_date(self):
        try:
            day: str = self.cleaned_data.get("end_date_day")
            month: str = self.cleaned_data.get("end_date_month")
            year: str = self.cleaned_data.get("end_date_year")
            return convert_day_month_year_to_date(day, month, year)
        except (ValueError, TypeError):
            return DEFAULT_END_DATE
