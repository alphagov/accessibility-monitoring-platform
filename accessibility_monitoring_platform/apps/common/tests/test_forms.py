"""
Test - common widgets and forms
"""

import logging
from datetime import date, datetime
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from django import forms
from pytest_django.asserts import assertHTMLEqual

from ...cases.forms import CaseMetadataUpdateForm
from ...cases.models import Case
from ..forms import (
    AMPCharField,
    AMPCharFieldWide,
    AMPChoiceCheckboxField,
    AMPChoiceCheckboxWidget,
    AMPChoiceField,
    AMPChoiceRadioField,
    AMPDateCheckboxWidget,
    AMPDateField,
    AMPDatePageCompleteField,
    AMPDateRangeForm,
    AMPDateWidget,
    AMPNewPasswordField,
    AMPPasswordField,
    AMPRadioSelectWidget,
    AMPTextField,
)
from ..models import Boolean

EXPECTED_RADIO_SELECT_WIDGET_HTML: str = """
<div class="govuk-radios">
    <div class="govuk-radios__item">
        <input class="govuk-radios__input" type="radio" name="name" value="val1">
        <label class="govuk-label govuk-radios__label">Label1</label>
    </div>
</div>"""

EXPECTED_CHECKBOX_WIDGET_HTML: str = """
<div class="govuk-checkboxes__item">
    <input class="govuk-checkboxes__input" type="checkbox" name="name">
    <label class="govuk-label govuk-checkboxes__label">Label text</label>
</div>"""

EXPECTED_DATE_WIDGET_HTML: str = """
<div class="govuk-date-input">
    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label">
                Day
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-2" type="number" name="name_0" class="govuk-input govuk-date-input__input govuk-input--width-2" pattern="[0-9]*" inputmode="numeric" />
        </div>
    </div>

    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label">
                Month
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-2" type="number" name="name_1" class="govuk-input govuk-date-input__input govuk-input--width-2" pattern="[0-9]*" inputmode="numeric" />
        </div>
    </div>

    <div class="govuk-date-input__item">
        <div class="govuk-form-group">
            <label class="govuk-label govuk-date-input__label">
                Year
            </label>
            <input class="govuk-input govuk-date-input__input govuk-input--width-4" type="number" name="name_2" class="govuk-input govuk-date-input__input govuk-input--width-4" pattern="[0-9]*" inputmode="numeric" />
        </div>
    </div>
</div>

<p class="govuk-body-m amp-margin-top-10 amp-margin-bottom-0">
    <span class="amp-control amp-populate-date-today" tabIndex="0" dayFieldId="" monthFieldId="" yearFieldId="">
        Populate with today\'s date
    </span>
</p>"""


class MockForm(forms.Form):
    """Form used to test fields and widgets"""

    date_as_checkbox = AMPDatePageCompleteField(label="Label1")
    choice_as_checkbox = AMPChoiceCheckboxField(label="Label2", choices=Boolean.choices)


def test_amp_widget_html_uses_govuk_classes():
    """Check widget renders the expected HTML"""
    widget: AMPRadioSelectWidget = AMPRadioSelectWidget(choices=[("val1", "Label1")])
    assertHTMLEqual(widget.render("name", None), EXPECTED_RADIO_SELECT_WIDGET_HTML)


def test_amp_checkbox_widget_html_uses_govuk_classes():
    """Check AMPChoiceCheckboxWidget renders the expected HTML"""
    widget: AMPChoiceCheckboxWidget = AMPChoiceCheckboxWidget(
        attrs={"label": "Label text"}
    )
    assertHTMLEqual(widget.render("name", None), EXPECTED_CHECKBOX_WIDGET_HTML)


def test_amp_date_checkbox_widget_html_uses_govuk_classes():
    """Check AMPDateCheckboxWidget renders the expected HTML"""
    widget: AMPDateCheckboxWidget = AMPDateCheckboxWidget(attrs={"label": "Label text"})
    assertHTMLEqual(widget.render("name", None), EXPECTED_CHECKBOX_WIDGET_HTML)


def test_amp_date_widget_html_uses_govuk_classes():
    """Check AMPDateWidget renders the expected HTML"""
    widget: AMPDateWidget = AMPDateWidget()
    assertHTMLEqual(widget.render("name", None), EXPECTED_DATE_WIDGET_HTML)


def test_amp_date_widget_html_includes_populate_today_control():
    """Check AMPDateWidget renders the expected controls"""
    widget: AMPDateWidget = AMPDateWidget()
    html: str = widget.render("name", None)
    assert "Populate with today's date" in html
    assert "amp-populate-date-today" in html
    assert "Populate date with one week from today" not in html
    assert "amp-populate-date-1-week" not in html
    assert "Populate date with four weeks from today" not in html
    assert "amp-populate-date-4-weeks" not in html
    assert "Populate date with 12 weeks from today" not in html
    assert "amp-populate-date-124-weeks" not in html


def test_amp_date_widget_html_includes_populate_future_dates_controls():
    """Check AMPDateWidget renders the expected controls"""
    widget: AMPDateWidget = AMPDateWidget(attrs={"populate_with_future_dates": True})
    html: str = widget.render("name", None)
    assert "Populate with today's date" not in html
    assert "amp-populate-date-today" not in html
    assert "Populate date with one week from today" in html
    assert "amp-populate-date-1-week" in html
    assert "Populate date with four weeks from today" in html
    assert "amp-populate-date-4-weeks" in html
    assert "Populate date with 12 weeks from today" in html
    assert "amp-populate-date-12-weeks" in html


@pytest.mark.parametrize(
    "field_class, expected_superclass",
    [
        (AMPCharField, forms.CharField),
        (AMPCharFieldWide, forms.CharField),
        (AMPTextField, forms.CharField),
        (AMPChoiceField, forms.ChoiceField),
        (AMPChoiceRadioField, forms.ChoiceField),
        (AMPDateField, forms.DateField),
        (AMPPasswordField, forms.CharField),
        (AMPNewPasswordField, forms.CharField),
    ],
)
def test_amp_field_class_subclasses_expected_class(field_class, expected_superclass):
    """Check field class is a subclass of expected class"""
    assert issubclass(field_class, expected_superclass)


@pytest.mark.parametrize(
    "field_class",
    [
        AMPCharField,
        AMPCharFieldWide,
        AMPTextField,
        AMPChoiceField,
        AMPChoiceRadioField,
        AMPDateField,
    ],
)
def test_amp_field_is_not_required(field_class):
    """Check field class defaults to not being required"""
    field: forms.Field = field_class(label="Label text")
    assert not field.required


@pytest.mark.parametrize(
    "field_class, expected_widget",
    [
        (AMPCharField, forms.TextInput),
        (AMPCharFieldWide, forms.TextInput),
        (AMPTextField, forms.Textarea),
        (AMPChoiceField, forms.Select),
        (AMPChoiceRadioField, AMPRadioSelectWidget),
        (AMPDateField, AMPDateWidget),
        (AMPPasswordField, forms.PasswordInput),
        (AMPNewPasswordField, forms.PasswordInput),
    ],
)
def test_amp_field_uses_expected_widget(field_class, expected_widget):
    """Check field uses expected widget"""
    field: forms.Field = field_class(label="Label text")
    assert isinstance(field.widget, expected_widget)


def test_amp_char_field_max_length():
    """Check AMPCharField defaults a max_length of 100"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert field.max_length == 100


def test_amp_char_field_widget_attrs():
    """Check AMPCharField widget attr defaults"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert field.widget.attrs == {
        "class": "govuk-input govuk-input--width-10",
        "maxlength": "100",
    }


def test_amp_char_field_wide_has_no_max_length():
    """Check AMPCharFieldWide has no default max_length"""
    field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")
    assert field.max_length is None


def test_amp_char_field_wide_widget_attrs():
    """Check AMPCharFieldWide widget attr defaults"""
    field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")
    assert field.widget.attrs == {"class": "govuk-input"}


def test_amp_text_field_widget_attrs():
    """Check AMPTextField widget attr defaults"""
    field: AMPTextField = AMPTextField(label="Label text")
    assert field.widget.attrs == {"class": "govuk-textarea", "cols": "40", "rows": "4"}


def test_amp_choice_field_widget_attrs():
    """Check AMPChoiceField widget attr defaults"""
    field: AMPChoiceField = AMPChoiceField(label="Label text")
    assert field.widget.attrs == {"class": "govuk-select"}


def test_amp_date_field_widget_attrs():
    """Check AMPDateField widget has no default attrs"""
    field: AMPDateField = AMPDateField(label="Label text")
    assert field.widget.attrs == {}


def test_amp_password_field_widget_attrs():
    """Check AMPPasswordField widget attr defaults"""
    field: AMPPasswordField = AMPPasswordField(label="Label text")
    assert field.widget.attrs == {"class": "govuk-input"}


def test_amp_new_password_field_widget_attrs():
    """Check AMPNewPasswordField widget attr defaults"""
    field: AMPNewPasswordField = AMPNewPasswordField(label="Label text")
    assert field.widget.attrs == {
        "autocomplete": "new-password",
        "class": "govuk-input",
    }


def test_amp_date_range_form_valid_dates():
    """Tests if form.is_valid() is true for valid dates"""
    form: AMPDateRangeForm = AMPDateRangeForm(
        data={
            "start_date_0": "31",
            "start_date_1": "12",
            "start_date_2": "2000",
            "end_date_0": "31",
            "end_date_1": "12",
            "end_date_2": "2100",
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["start_date"] == datetime(
        year=2000, month=12, day=31, tzinfo=ZoneInfo("UTC")
    )
    assert form.cleaned_data["end_date"] == datetime(
        year=2100,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        tzinfo=ZoneInfo("UTC"),
    )


def test_amp_date_range_form_fails_invalid_start_date():
    """Tests if form.is_valid() is false if start date is invalid"""
    form: AMPDateRangeForm = AMPDateRangeForm(
        data={
            "start_date_0": "31",
            "start_date_1": "2",
            "start_date_2": "1900",
            "end_date_0": "1",
            "end_date_1": "1",
            "end_date_2": "2100",
        }
    )
    assert not form.is_valid()


def test_amp_date_range_form_fails_invalid_end_date_year():
    """Tests if form.is_valid() is false if end date is invalid"""
    form: AMPDateRangeForm = AMPDateRangeForm(
        data={
            "start_date_0": "1",
            "start_date_1": "1",
            "start_date_2": "1900",
            "end_date_0": "31",
            "end_date_1": "2",
            "end_date_2": "2100",
        }
    )
    assert not form.is_valid()


def test_amp_choice_checkbox_field_and_widget_return_yes_when_checked():
    """Tests AMPChoiceCheckboxField and AMPChoiceCheckboxWidget return 'yes' when checked"""
    form: MockForm = MockForm(
        data={
            "choice_as_checkbox": "on",
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["choice_as_checkbox"] == "yes"


def test_amp_choice_checkbox_field_and_widget_return_no_when_not_checked():
    """Tests AMPChoiceCheckboxField and AMPChoiceCheckboxWidget return 'no' when not checked"""
    form: MockForm = MockForm(data={})
    assert form.is_valid()
    assert form.cleaned_data["choice_as_checkbox"] == "no"


def test_amp_date_sent_field_and_widget_return_today_when_checked():
    """Tests AMPDatePageCompleteField and AMPDateCheckboxWidget return today when checked"""
    form: MockForm = MockForm(
        data={
            "date_as_checkbox": "on",
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["date_as_checkbox"] == date.today()


def test_amp_date_sent_field_and_widget_return_none_when_not_checked():
    """Tests AMPDatePageCompleteField and AMPDateCheckboxWidget return none when not checked"""
    form: MockForm = MockForm(data={})
    assert form.is_valid()
    assert form.cleaned_data["date_as_checkbox"] is None


def test_version_form():
    """Test version form returns and logs version errors"""
    case: Case = Case()
    version_form: CaseMetadataUpdateForm = CaseMetadataUpdateForm(
        data={"version": 1}, instance=case
    )

    logger = logging.getLogger("accessibility_monitoring_platform.apps.common.forms")
    with mock.patch.object(logger, "error") as mock_error_logger:
        version_form.is_valid()
        mock_error_logger.assert_called_once_with(
            "%s has changed since page loaded", case
        )
