"""
Common widgets and form fields
"""
from datetime import date, datetime
import pytz
from typing import Any, Dict, Iterable, List, Mapping, Union

from django.contrib.auth.models import User
from django import forms

from .utils import convert_date_to_datetime

DEFAULT_START_DATE: datetime = datetime(year=1900, month=1, day=1, tzinfo=pytz.UTC)
DEFAULT_END_DATE: datetime = datetime(year=2100, month=1, day=1, tzinfo=pytz.UTC)


class AMPRadioSelectWidget(forms.RadioSelect):
    """ Override widget template for forms.RadioSelect """

    template_name = "common/amp_radio_select_widget_template.html"


class AMPCheckboxWidget(forms.CheckboxInput):
    """ Override widget template for forms.CheckboxInput """

    template_name = "common/amp_checkbox_widget_template.html"


class AMPCheckboxSelectMultipleWidget(forms.CheckboxSelectMultiple):
    """ Override widget template for forms.CheckboxSelectMultiple """

    template_name = "common/amp_checkbox_select_multiple_widget_template.html"


class AMPDateWidget(forms.MultiWidget):
    """ Widget for GDS design system date fields """

    template_name = "common/amp_date_widget_template.html"

    def __init__(self, attrs=None) -> None:
        day_widget_attrs = {
            "label": "Day",
            "class": "govuk-input govuk-date-input__input govuk-input--width-2",
            "type": "number",
            "pattern": "[0-9]*",
            "inputmode": "numeric",
        }
        month_specific_attrs = {
            "label": "Month",
        }
        year_specific_attrs = {
            "label": "Year",
            "class": "govuk-input govuk-date-input__input govuk-input--width-4",
        }
        widgets = [
            forms.NumberInput(attrs=day_widget_attrs),
            forms.NumberInput(attrs={**day_widget_attrs, **month_specific_attrs}),
            forms.NumberInput(attrs={**day_widget_attrs, **year_specific_attrs}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value: Union[date, str]) -> List[Union[int, str, None]]:
        """
        Break date or hyphen-delimited string into into day, month and year integer values.

        If no values are found then return three Nones.
        """
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str):
            if value == "":
                return [None, None, None]
            year, month, day = value.split("-")
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(
        self, data: Dict[str, Any], files: Mapping[str, Iterable[Any]], name: str
    ) -> str:
        """
        Return day, month and year integer values and return as
        hyphen-delimited string.

        If no values are found return empty string.
        """
        day, month, year = super().value_from_datadict(data, files, name)
        if day is None and month is None and year is None:
            return ""
        if day == "" and month == "" and year == "":
            return ""
        return "{}-{}-{}".format(year, month, day)


class AMPCharField(forms.CharField):
    """ Adds default max_length and widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault(
            "widget",
            forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        )
        super().__init__(*args, **kwargs)


class AMPCharFieldWide(forms.CharField):
    """ Adds default widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.TextInput(attrs={"class": "govuk-input"}),
        )
        super().__init__(*args, **kwargs)


class AMPTextField(forms.CharField):
    """ Adds default widget to Django forms TextField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Textarea(attrs={"class": "govuk-textarea", "rows": "2"}),
        )
        super().__init__(*args, **kwargs)


class AMPChoiceField(forms.ChoiceField):
    """ Adds default widget to Django forms ChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Select(attrs={"class": "govuk-select"}),
        )
        super().__init__(*args, **kwargs)


class AMPModelChoiceField(forms.ModelChoiceField):
    """ Adds default widget to Django forms ModelChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Select(attrs={"class": "govuk-select"}),
        )
        super().__init__(*args, **kwargs)


class AMPUserModelChoiceField(forms.ModelChoiceField):
    """
    Adds default widget to Django forms ModelChoiceField for use with User model.

    Uses user's full name as label.
    """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Select(attrs={"class": "govuk-select"}),
        )
        kwargs.setdefault(
            "queryset", User.objects.all().order_by("first_name", "last_name")
        )
        super().__init__(*args, **kwargs)

    def label_from_instance(self, user):
        """ Return full name from user """
        return user.get_full_name()


class AMPModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ Adds default widget to Django forms ModelMultipleChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", AMPCheckboxSelectMultipleWidget())
        super().__init__(*args, **kwargs)


class AMPBooleanField(forms.BooleanField):
    """ Adds default widget to Django forms BooleanField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", AMPCheckboxWidget())
        super().__init__(*args, **kwargs)


class AMPDateField(forms.DateField):
    """ Adds default widget to Django forms DateField """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", AMPDateWidget())
        super().__init__(*args, **kwargs)


class AMPDateRangeForm(forms.Form):
    """
    Form used to filter by date range.
    Start and end dates default to span entire period.
    """

    start_date = forms.DateField(
        label="Start date", widget=AMPDateWidget(), required=False
    )
    end_date = forms.DateField(label="End date", widget=AMPDateWidget(), required=False)

    def clean_start_date(self) -> datetime:
        """ Returns default start date or converts entered date to datetime """
        start_date = self.cleaned_data["start_date"]
        if start_date:
            return convert_date_to_datetime(start_date)
        return DEFAULT_START_DATE

    def clean_end_date(self) -> datetime:
        """ Returns default end date or converts entered date to datetime """
        end_date = self.cleaned_data["end_date"]
        if end_date:
            return convert_date_to_datetime(end_date)
        return DEFAULT_END_DATE
