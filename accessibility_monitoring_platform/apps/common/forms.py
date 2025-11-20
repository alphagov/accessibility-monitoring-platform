"""
Common widgets and form fields
"""

import logging
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from django import forms
from django.contrib.auth.models import User

from .models import FooterLink, FrequentlyUsedLink, Platform
from .utils import convert_date_to_datetime, validate_url

DEFAULT_START_DATE: datetime = datetime(
    year=1900, month=1, day=1, tzinfo=ZoneInfo("UTC")
)
DEFAULT_END_DATE: datetime = datetime(year=2100, month=1, day=1, tzinfo=ZoneInfo("UTC"))
LOG_LEVEL_CHOICES: list[tuple[int, str]] = [
    (logging.WARNING, "Warning"),
    (logging.ERROR, "Error"),
    (logging.CRITICAL, "Critical"),
]
IMPORT_MODEL_CHOICES: list[tuple[int, str]] = [
    ("detailed", "Detailed testing case"),
    ("mobile", "Mobile testing case"),
]

logger = logging.getLogger(__name__)


class VersionForm(forms.ModelForm):
    """
    Form for checking version has not changed
    """

    version = forms.IntegerField(widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        version_on_form: int = int(cleaned_data.get("version", 0))
        if version_on_form != self.instance.version:
            self.add_error(
                None,
                f"{self.instance} has changed since this page loaded",
            )
            logger.error("%s has changed since page loaded", self.instance)
        return cleaned_data


class AMPURLWidget(forms.TextInput):
    """Widget for URL input field with dynamic clickable link"""

    template_name = "common/amp_url_field_dynamic_link.html"


class AMPRadioSelectWidget(forms.RadioSelect):
    """Widget for GDS design system radio button fields"""

    template_name = "common/amp_radio_select_widget_template.html"


class AMPBooleanCheckboxWidget(forms.CheckboxInput):
    """Widget for GDS design system checkbox fields with boolean data"""

    template_name = "common/amp_checkbox_widget_template.html"


class AMPChoiceCheckboxWidget(AMPBooleanCheckboxWidget):
    """Widget for GDS design system checkbox fields with choice data"""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value == "no":
            context["widget"]["attrs"]["checked"] = False
        return context

    def value_from_datadict(self, data, files, name):  # pylint: disable=unused-argument
        """If checkbox is ticked, return 'yes' otherwise return 'no'"""
        if name not in data:
            # A missing value means False because HTML form submission does not
            # send results for unselected checkboxes.
            return "no"
        return "yes"


class AMPDateCheckboxWidget(AMPChoiceCheckboxWidget):
    """Widget for GDS design system showing date field as checkbox"""

    def value_from_datadict(self, data, files, name):
        """If checkbox is ticked, return today's date"""
        if name not in data:
            return None
        return date.today()


class AMPCheckboxSelectMultipleWidget(forms.CheckboxSelectMultiple):
    """Widget for GDS design system multi-select checkboxes fields"""

    template_name = "common/amp_checkbox_select_multiple_widget_template.html"


class AMPDateWidget(forms.MultiWidget):
    """Widget for GDS design system date fields"""

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

    def decompress(self, value: date | str) -> list[int | str | None]:
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
        self, data: dict[str, Any], files: Mapping[str, Iterable[Any]], name: str
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
        return f"{year}-{month}-{day}"


class AMPIntegerField(forms.IntegerField):
    """Number input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.NumberInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        )
        super().__init__(*args, **kwargs)


class AMPCharField(forms.CharField):
    """Character input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault(
            "widget",
            forms.TextInput(attrs={"class": "govuk-input govuk-input--width-10"}),
        )
        super().__init__(*args, **kwargs)


class AMPCharFieldWide(forms.CharField):
    """Full width character input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.TextInput(attrs={"class": "govuk-input"}),
        )
        super().__init__(*args, **kwargs)


class AMPPasswordField(forms.CharField):
    """Password field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault(
            "widget",
            forms.PasswordInput(attrs={"class": "govuk-input"}),
        )
        super().__init__(*args, **kwargs)


class AMPNewPasswordField(forms.CharField):
    """New password field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("strip", False)
        kwargs.setdefault(
            "widget",
            forms.PasswordInput(
                attrs={"autocomplete": "new-password", "class": "govuk-input"}
            ),
        )
        super().__init__(*args, **kwargs)


class AMPURLField(forms.CharField):
    """Character input field with url validation in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            AMPURLWidget(attrs={"class": "govuk-input"}),
        )
        kwargs.setdefault("validators", [validate_url])
        super().__init__(*args, **kwargs)


class AMPTextField(forms.CharField):
    """Textarea input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Textarea(attrs={"class": "govuk-textarea", "rows": "4"}),
        )
        super().__init__(*args, **kwargs)


class AMPChoiceField(forms.ChoiceField):
    """Choice input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Select(attrs={"class": "govuk-select"}),
        )
        super().__init__(*args, **kwargs)


class AMPChoiceRadioField(AMPChoiceField):
    """Radio input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("widget", AMPRadioSelectWidget)
        super().__init__(*args, **kwargs)


class AMPChoiceCheckboxField(AMPChoiceField):
    """Checkbox input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("widget", AMPChoiceCheckboxWidget)
        super().__init__(*args, **kwargs)


class AMPModelChoiceField(forms.ModelChoiceField):
    """Model choice input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Select(attrs={"class": "govuk-select"}),
        )
        super().__init__(*args, **kwargs)


class AMPModelChoiceRadioField(forms.ModelChoiceField):
    """Model choice input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": AMPRadioSelectWidget(),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPAuditorModelChoiceField(AMPModelChoiceField):
    """
    Model choice input field in the style of GDS design system.

    Uses User model. Uses user's full name as label. Only members of Auditor group returned.
    """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault(
            "queryset",
            User.objects.filter(groups__name="Auditor").order_by(
                "first_name", "last_name"
            ),
        )
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        """Return full name from user"""
        return obj.get_full_name()


class AMPQAAuditorModelChoiceField(AMPAuditorModelChoiceField):
    """
    Model choice input field in the style of GDS design system.

    Uses User model. Uses user's full name as label. Only members of QA auditor group returned.
    """

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault(
            "queryset",
            User.objects.filter(groups__name="QA auditor").order_by(
                "first_name", "last_name"
            ),
        )
        super().__init__(*args, **kwargs)


class AMPModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Model multi-choice input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        default_kwargs: dict = {
            "widget": AMPCheckboxSelectMultipleWidget(),
            "required": False,
        }
        overridden_default_kwargs: dict = {**default_kwargs, **kwargs}
        super().__init__(*args, **overridden_default_kwargs)


class AMPDateField(forms.DateField):
    """Date input field in the style of GDS design system"""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", AMPDateWidget())
        super().__init__(*args, **kwargs)


class AMPDatePageCompleteField(forms.DateField):
    """Checkbox input field in the style of GDS design system. Stores today's date when ticked."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", "Mark this page as complete")
        kwargs.setdefault(
            "widget", AMPDateCheckboxWidget(attrs={"label": "Page complete"})
        )
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
        """Returns default start date or converts entered date to datetime"""
        start_date = self.cleaned_data["start_date"]
        if start_date:
            return convert_date_to_datetime(start_date)
        return DEFAULT_START_DATE

    def clean_end_date(self) -> datetime:
        """Returns default end date or converts entered date to datetime"""
        end_date = self.cleaned_data["end_date"]
        if end_date:
            return convert_date_to_datetime(end_date, hour=23, minute=59, second=59)
        return DEFAULT_END_DATE


class AMPContactAdminForm(forms.Form):
    """
    Form used to send message to platform admin.
    """

    subject = AMPCharFieldWide(label="Subject")
    message = AMPTextField(label="Message")


class PlatformCheckingForm(forms.Form):
    """
    Form used to write a log message.
    """

    level = AMPChoiceField(label="Level", choices=LOG_LEVEL_CHOICES)
    message = AMPCharFieldWide(label="Message", initial="Test log message")


class AMPTopMenuForm(forms.Form):
    """
    Form for searching for cases in the top menu bar
    """

    search = AMPCharField(
        widget=forms.TextInput(
            attrs={
                "class": "govuk-input amp-small-search",
                "placeholder": "Search",
            }
        )
    )


class ActiveQAAuditorUpdateForm(forms.ModelForm):
    """
    Form for updating the active QA auditor platform setting
    """

    active_qa_auditor = AMPQAAuditorModelChoiceField(label="Active QA auditor")

    class Meta:
        model = Platform
        fields = [
            "active_qa_auditor",
        ]


class FrequentlyUsedLinkUpdateForm(forms.ModelForm):
    """
    Form for updating a frequently used link
    """

    label = AMPCharFieldWide(label="Label")
    url = AMPURLField(label="URL")
    case_type = AMPChoiceRadioField(
        label="Type of case",
        choices=FrequentlyUsedLink.CaseType.choices,
        initial=FrequentlyUsedLink.CaseType.ALL,
    )

    class Meta:
        model = FrequentlyUsedLink
        fields = [
            "label",
            "url",
            "case_type",
        ]


FrequentlyUsedLinkFormset: Any = forms.modelformset_factory(
    FrequentlyUsedLink, FrequentlyUsedLinkUpdateForm, extra=0
)
FrequentlyUsedLinkOneExtraFormset: Any = forms.modelformset_factory(
    FrequentlyUsedLink, FrequentlyUsedLinkUpdateForm, extra=1
)


class FooterLinkUpdateForm(forms.ModelForm):
    """
    Form for updating a footer link
    """

    label = AMPCharFieldWide(label="Label")
    url = AMPURLField(label="URL")

    class Meta:
        model = FooterLink
        fields = [
            "label",
            "url",
        ]


FooterLinkFormset: Any = forms.modelformset_factory(
    FooterLink, FooterLinkUpdateForm, extra=0
)
FooterLinkOneExtraFormset: Any = forms.modelformset_factory(
    FooterLink, FooterLinkUpdateForm, extra=1
)


class BulkURLSearchForm(forms.Form):
    urls = AMPTextField(label="URLs")


class ImportCSVForm(forms.Form):
    model = AMPChoiceField(label="Model", choices=IMPORT_MODEL_CHOICES)
    data = AMPTextField(label="CSV data")


class ImportTrelloCommentsForm(forms.Form):
    data = AMPTextField(label="CSV data")
