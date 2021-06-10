"""
Common widgets and form fields
"""
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Union

from django import forms


DEFAULT_START_DATE: date = date(year=1900, month=1, day=1)
DEFAULT_END_DATE: date = date(year=2100, month=1, day=1)


class AMPSelectWidget(forms.RadioSelect):
    template_name = "common/amp_select_widget_template.html"


class AMPRadioSelectWidget(forms.RadioSelect):
    template_name = "common/amp_radio_select_widget_template.html"


class AMPCheckboxWidget(forms.CheckboxInput):
    template_name = "common/amp_checkbox_widget_template.html"


class AMPCheckboxSelectMultipleWidget(forms.CheckboxSelectMultiple):
    template_name = "common/amp_checkbox_select_multiple_widget_template.html"


class AMPDateWidget(forms.MultiWidget):
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
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str) and value != "":
            year, month, day = value.split("-")
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(
        self, data: Dict[str, Any], files: Mapping[str, Iterable[Any]], name: str
    ) -> str:
        day, month, year = super().value_from_datadict(data, files, name)
        if day == "" and month == "" and year == "":
            return ""
        return "{}-{}-{}".format(year, month, day)


class AMPCharField(forms.CharField):
    """ Adds default max_length and widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "max_length": 100,
            "widget": forms.TextInput(
                attrs={"class": "govuk-input govuk-input--width-10"}
            ),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPCharFieldWide(forms.CharField):
    """ Adds default widget to Django forms CharField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.TextInput(attrs={"class": "govuk-input"}),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPTextField(forms.CharField):
    """ Adds default widget to Django forms TextField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.Textarea(attrs={"class": "govuk-textarea", "rows": "2"}),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPChoiceField(forms.ChoiceField):
    """ Adds default widget to Django forms ChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.Select(attrs={"class": "govuk-select"}),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ Adds default widget to Django forms ModelMultipleChoiceField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": AMPCheckboxSelectMultipleWidget(),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPBooleanField(forms.BooleanField):
    """ Adds default widget to Django forms BooleanField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": forms.CheckboxInput(attrs={"class": "govuk-checkboxes__input"}),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPDateField(forms.DateField):
    """ Adds default widget to Django forms DateField """

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": AMPDateWidget(),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPDateRangeForm(forms.Form):
    """
    Form used to filter by date range.
    Start and end dates default to span entire period.
    """

    start_date = forms.DateField(
        label="Start date", widget=AMPDateWidget(), required=False
    )
    end_date = forms.DateField(label="End date", widget=AMPDateWidget(), required=False)

    def clean(self) -> Dict[str, Any]:
        cleaned_data: dict = super().clean()
        if "start_date" not in cleaned_data or not cleaned_data["start_date"]:
            cleaned_data["start_date"] = DEFAULT_START_DATE
        if "end_date" not in cleaned_data or not cleaned_data["end_date"]:
            cleaned_data["end_date"] = DEFAULT_END_DATE
        return cleaned_data
