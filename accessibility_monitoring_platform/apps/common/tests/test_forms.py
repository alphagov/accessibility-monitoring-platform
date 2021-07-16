"""
Test - common widgets and forms
"""
from datetime import date, datetime
import pytz

from pytest_django.asserts import assertHTMLEqual

from django import forms

from ..forms import (
    AMPRadioSelectWidget,
    AMPCheckboxWidget,
    AMPDateCheckboxWidget,
    AMPDateWidget,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPBooleanField,
    AMPNullableBooleanField,
    AMPDateField,
    AMPDateSentField,
    AMPDateRangeForm,
)

EXPECTED_RADIO_SELECT_WIDGET_HTML: str = """
<div class="govuk-radios">
    <div class="govuk-radios__item">
        <input class="govuk-radios__input" type="radio" name="name" value="val1">
        <label class="govuk-label govuk-radios__label">Label1</label>
    </div>
</div>"""

EXPECTED_CHECKBOX_WIDGET_HTML: str = """
<div class="govuk-checkboxes__item">
    <input class="govuk-checkboxes__input" type="checkbox" name="name" label="Label text">
    <label class="govuk-label govuk-checkboxes__label">Label text</label>
</div>"""

EXPECTED_DATE_WIDGET_HTML: str = """
<div class="govuk-date-input">
        <div class="govuk-date-input__item">
            <div class="govuk-form-group">
                <label class="govuk-label govuk-date-input__label">Day</label>
                <input
                    class="govuk-input govuk-date-input__input govuk-input--width-2"
                    type="number"
                    name="name_0"
                    label="Day"
                    class="govuk-input govuk-date-input__input govuk-input--width-2"
                    pattern="[0-9]*"
                    inputmode="numeric">
            </div>
        </div>
        <div class="govuk-date-input__item">
            <div class="govuk-form-group">
                <label class="govuk-label govuk-date-input__label">Month</label>
                <input
                    class="govuk-input govuk-date-input__input govuk-input--width-2"
                    type="number"
                    name="name_1"
                    label="Month"
                    class="govuk-input govuk-date-input__input govuk-input--width-2"
                    pattern="[0-9]*"
                    inputmode="numeric">
            </div>
        </div>
        <div class="govuk-date-input__item">
            <div class="govuk-form-group">
                <label class="govuk-label govuk-date-input__label">Year</label>
                <input
                    class="govuk-input govuk-date-input__input govuk-input--width-4"
                    type="number"
                    name="name_2"
                    label="Year"
                    class="govuk-input govuk-date-input__input govuk-input--width-4"
                    pattern="[0-9]*"
                    inputmode="numeric">
            </div>
        </div>
</div>"""


class MockForm(forms.Form):
    """Form used to test fields and widgets"""

    date_as_checkbox = AMPDateSentField(label="Label1")


def test_amp_radio_select_widget_html_uses_govuk_classes():
    """Check AMPRadioSelectWidget renders the expected HTML"""
    widget: AMPRadioSelectWidget = AMPRadioSelectWidget(choices=[("val1", "Label1")])
    assertHTMLEqual(widget.render("name", None), EXPECTED_RADIO_SELECT_WIDGET_HTML)


def test_amp_checkbox_widget_html_uses_govuk_classes():
    """Check AMPCheckboxWidget renders the expected HTML"""
    widget: AMPCheckboxWidget = AMPCheckboxWidget(attrs={"label": "Label text"})
    assertHTMLEqual(widget.render("name", None), EXPECTED_CHECKBOX_WIDGET_HTML)


def test_amp_date_checkbox_widget_html_uses_govuk_classes():
    """Check AMPDateCheckboxWidget renders the expected HTML"""
    widget: AMPDateCheckboxWidget = AMPDateCheckboxWidget(attrs={"label": "Label text"})
    assertHTMLEqual(widget.render("name", None), EXPECTED_CHECKBOX_WIDGET_HTML)


def test_amp_date_widget_html_uses_govuk_classes():
    """Check AMPDateWidget renders the expected HTML"""
    widget: AMPDateWidget = AMPDateWidget()
    assertHTMLEqual(widget.render("name", None), EXPECTED_DATE_WIDGET_HTML)


def test_amp_char_field_class_is_a_subclass_of_charfield():
    """Check AMPCharField is a subclass of forms.CharField"""
    assert issubclass(AMPCharField, forms.CharField)


def test_amp_char_field_is_not_required():
    """Check AMPCharField defaults to not being required"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert not field.required


def test_amp_char_field_max_length():
    """Check AMPCharField defaults a max_length of 100"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert field.max_length == 100


def test_amp_char_field_widget():
    """Check AMPCharField uses widget forms.TextInput"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert isinstance(field.widget, forms.TextInput)


def test_amp_char_field_widget_attrs():
    """Check AMPCharField widget attr defaults"""
    field: AMPCharField = AMPCharField(label="Label text")
    assert field.widget.attrs == {
        "class": "govuk-input govuk-input--width-10",
        "maxlength": "100",
    }


def test_amp_char_field_wide_class_is_a_subclass_of_charfield():
    """Check AMPCharFieldWide is a subclass of forms.CharField"""
    assert issubclass(AMPCharFieldWide, forms.CharField)


def test_amp_char_field_wide_is_not_required():
    """Check AMPCharField defaults to not being required"""
    field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")
    assert not field.required


def test_amp_char_field_wide_has_no_max_length():
    """Check AMPCharFieldWide has no default max_length"""
    field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")
    assert field.max_length is None


def test_amp_char_field_wide_widget_attrs():
    """Check AMPCharFieldWide widget attr defaults"""
    field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")
    assert field.widget.attrs == {"class": "govuk-input"}


def test_amp_text_field_class_is_a_subclass_of_charfield():
    """Check AMPTextField is a subclass of forms.CharField"""
    assert issubclass(AMPTextField, forms.CharField)


def test_amp_text_field_is_not_required():
    """Check AMPTextField defaults to not being required"""
    field: AMPTextField = AMPTextField(label="Label text")
    assert not field.required


def test_amp_text_field_widget():
    """Check AMPTextField uses widget forms.Textarea"""
    field: AMPTextField = AMPTextField(label="Label text")
    assert isinstance(field.widget, forms.Textarea)


def test_amp_text_field_widget_attrs():
    """Check AMPTextField widget attr defaults"""
    field: AMPTextField = AMPTextField(label="Label text")
    assert field.widget.attrs == {"class": "govuk-textarea", "cols": "40", "rows": "2"}


def test_amp_choice_field_class_is_a_subclass_of_choicefield():
    """Check AMPChoiceField is a subclass of forms.ChoiceField"""
    assert issubclass(AMPChoiceField, forms.ChoiceField)


def test_amp_choice_field_is_not_required():
    """Check AMPChoiceField defaults to not being required"""
    field: AMPChoiceField = AMPChoiceField(label="Label text")
    assert not field.required


def test_amp_choice_field_widget():
    """Check AMPChoiceField uses widget forms.Select"""
    field: AMPChoiceField = AMPChoiceField(label="Label text")
    assert isinstance(field.widget, forms.Select)


def test_amp_choice_field_widget_attrs():
    """Check AMPChoiceField widget attr defaults"""
    field: AMPChoiceField = AMPChoiceField(label="Label text")
    assert field.widget.attrs == {"class": "govuk-select"}


def test_amp_boolean_field_class_is_a_subclass_of_booleanfield():
    """Check AMPBooleanField is a subclass of forms.BooleanField"""
    assert issubclass(AMPBooleanField, forms.BooleanField)


def test_amp_boolean_field_is_not_required():
    """Check AMPBooleanField defaults to not being required"""
    field: AMPBooleanField = AMPBooleanField(label="Label text")
    assert not field.required


def test_amp_boolean_field_widget():
    """Check AMPBooleanField uses widget AMPCheckboxWidget"""
    field: AMPBooleanField = AMPBooleanField(label="Label text")
    assert isinstance(field.widget, AMPCheckboxWidget)


def test_amp_nullable_boolean_field_class_is_a_subclass_of_choicefield():
    """Check AMPNullableBooleanField is a subclass of forms.ChoiceField"""
    assert issubclass(AMPNullableBooleanField, forms.ChoiceField)


def test_amp_nullable_boolean_field_is_not_required():
    """Check AMPNullableBooleanField defaults to not being required"""
    field: AMPNullableBooleanField = AMPNullableBooleanField(label="Label text")
    assert not field.required


def test_amp_nullable_boolean_field_widget():
    """Check AMPNullableBooleanField uses widget AMPRadioSelectWidget"""
    field: AMPNullableBooleanField = AMPNullableBooleanField(label="Label text")
    assert isinstance(field.widget, AMPRadioSelectWidget)


def test_amp_date_field_class_is_a_subclass_of_datefield():
    """Check AMPDateField is a subclass of forms.DateField"""
    assert issubclass(AMPDateField, forms.DateField)


def test_amp_date_field_is_not_required():
    """Check AMPDateField defaults to not being required"""
    field: AMPDateField = AMPDateField(label="Label text")
    assert not field.required


def test_amp_date_field_widget():
    """Check AMPDateField uses widget AMPDateWidget"""
    field: AMPDateField = AMPDateField(label="Label text")
    assert isinstance(field.widget, AMPDateWidget)


def test_amp_date_field_widget_attrs():
    """Check AMPDateField widget has no default attrs"""
    field: AMPDateField = AMPDateField(label="Label text")
    assert field.widget.attrs == {}


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
        year=2000, month=12, day=31, tzinfo=pytz.UTC
    )
    assert form.cleaned_data["end_date"] == datetime(
        year=2100, month=12, day=31, hour=23, minute=59, second=59, tzinfo=pytz.UTC
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


def test_amp_date_sent_field_and_widget_return_today_when_checked():
    """Tests AMPDateSentField and AMPDateCheckboxWidget return today when checked"""
    form: MockForm = MockForm(
        data={
            "date_as_checkbox": "on",
        }
    )
    assert form.is_valid()
    assert form.cleaned_data["date_as_checkbox"] == date.today()


def test_amp_date_sent_field_and_widget_return_none_when_not_checked():
    """Tests AMPDateSentField and AMPDateCheckboxWidget return none when not checked"""
    form: MockForm = MockForm(data={})
    assert form.is_valid()
    assert form.cleaned_data["date_as_checkbox"] is None
