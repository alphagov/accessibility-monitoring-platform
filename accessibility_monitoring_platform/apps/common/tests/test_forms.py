"""
Test - common widgets and forms
"""
from django import forms
from django.test import TestCase
from django.test.client import RequestFactory

from ..forms import (
    AMPRadioSelectWidget,
    AMPCheckboxWidget,
    AMPDateWidget,
    AMPCharField,
    AMPCharFieldWide,
    AMPTextField,
    AMPChoiceField,
    AMPBooleanField,
    AMPDateField,
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


class AMPRadioSelectWidgetTestCase(TestCase):
    """ Test output of AMPRadioSelectWidget """

    def test_html_uses_govuk_classes(self):
        """ Check AMPRadioSelectWidget renders the expected HTML """
        widget: AMPRadioSelectWidget = AMPRadioSelectWidget(
            choices=[("val1", "Label1")]
        )
        self.assertHTMLEqual(
            widget.render("name", None), EXPECTED_RADIO_SELECT_WIDGET_HTML
        )


class AMPCheckboxWidgetWidgetTestCase(TestCase):
    """ Test output of AMPCheckboxWidget """

    def test_html_uses_govuk_classes(self):
        """ Check AMPCheckboxWidget renders the expected HTML """
        widget: AMPCheckboxWidget = AMPCheckboxWidget(attrs={"label": "Label text"})
        self.assertHTMLEqual(widget.render("name", None), EXPECTED_CHECKBOX_WIDGET_HTML)


class AMPDateWidgetTestCase(TestCase):
    """ Test output of AMPDateWidget """

    def test_html_uses_govuk_classes(self):
        """ Check AMPDateWidget renders the expected HTML """
        widget: AMPDateWidget = AMPDateWidget()
        self.assertHTMLEqual(widget.render("name", None), EXPECTED_DATE_WIDGET_HTML)


class AMPCharFieldTestCase(TestCase):
    """ Test AMPCharField """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPCharField = AMPCharField(label="Label text")

    def test_field_class_is_a_subclass_of_charfield(self):
        """ Check AMPCharField is a subclass of forms.CharField """
        self.assertTrue(issubclass(AMPCharField, forms.CharField))

    def test_field_is_not_required(self):
        """ Check AMPCharField defaults to not being required """
        self.assertEqual(self.field.required, False)

    def test_field_max_length(self):
        """ Check AMPCharField defaults a max_length of 100 """
        self.assertEqual(self.field.max_length, 100)

    def test_field_widget(self):
        """ Check AMPCharField uses widget forms.TextInput """
        self.assertEqual(type(self.field.widget), forms.TextInput)

    def test_field_widget_attrs(self):
        """ Check AMPCharField widget attr defaults """
        self.assertEqual(
            self.field.widget.attrs,
            {"class": "govuk-input govuk-input--width-10", "maxlength": "100"},
        )


class AMPCharFieldWideTestCase(AMPCharFieldTestCase):
    """ Test AMPCharFieldWide """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPCharFieldWide = AMPCharFieldWide(label="Label text")

    def test_field_max_length(self):
        """ Check AMPCharFieldWide has no default max_length """
        self.assertEqual(self.field.max_length, None)

    def test_field_widget_attrs(self):
        """ Check AMPCharFieldWide widget attr defaults """
        self.assertEqual(self.field.widget.attrs, {"class": "govuk-input"})


class AMPTextFieldTestCase(TestCase):
    """ Test AMPTextField """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPTextField = AMPTextField(label="Label text")

    def test_field_class_is_a_subclass_of_charfield(self):
        """ Check AMPTextField is a subclass of forms.CharField """
        self.assertTrue(issubclass(AMPTextField, forms.CharField))

    def test_field_is_not_required(self):
        """ Check AMPTextField defaults to not being required """
        self.assertEqual(self.field.required, False)

    def test_field_widget(self):
        """ Check AMPTextField uses widget forms.Textarea """
        self.assertEqual(type(self.field.widget), forms.Textarea)

    def test_field_widget_attrs(self):
        """ Check AMPTextField widget attr defaults """
        self.assertEqual(
            self.field.widget.attrs,
            {"class": "govuk-textarea", "cols": "40", "rows": "2"},
        )


class AMPChoiceFieldTestCase(TestCase):
    """ Test AMPChoiceField """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPChoiceField = AMPChoiceField(label="Label text")

    def test_field_class_is_a_subclass_of_choicefield(self):
        """ Check AMPChoiceField is a subclass of forms.ChoiceField """
        self.assertTrue(issubclass(AMPChoiceField, forms.ChoiceField))

    def test_field_is_not_required(self):
        """ Check AMPChoiceField defaults to not being required """
        self.assertEqual(self.field.required, False)

    def test_field_widget(self):
        """ Check AMPChoiceField uses widget forms.Select """
        self.assertEqual(type(self.field.widget), forms.Select)

    def test_field_widget_attrs(self):
        """ Check AMPTextField widget attr defaults """
        self.assertEqual(self.field.widget.attrs, {"class": "govuk-select"})


class AMPBooleanFieldTestCase(TestCase):
    """ Test AMPBooleanField """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPBooleanField = AMPBooleanField(label="Label text")

    def test_field_class_is_a_subclass_of_booleanfield(self):
        """ Check AMPBooleanField is a subclass of forms.BooleanField """
        self.assertTrue(issubclass(AMPBooleanField, forms.BooleanField))

    def test_field_is_not_required(self):
        """ Check AMPBooleanField defaults to not being required """
        self.assertEqual(self.field.required, False)

    def test_field_widget(self):
        """ Check AMPBooleanField uses widget forms.CheckboxInput """
        self.assertEqual(type(self.field.widget), forms.CheckboxInput)

    def test_field_widget_attrs(self):
        """ Check AMPBooleanField widget attr defaults """
        self.assertEqual(self.field.widget.attrs, {"class": "govuk-checkboxes__input"})


class AMPDateFieldTestCase(TestCase):
    """ Test AMPDateField """

    def setUp(self):
        """ Sets up the test environment with a field """
        self.field: AMPDateField = AMPDateField(label="Label text")

    def test_field_class_is_a_subclass_of_datefield(self):
        """ Check AMPDateField is a subclass of forms.DateField """
        self.assertTrue(issubclass(AMPDateField, forms.DateField))

    def test_field_is_not_required(self):
        """ Check AMPDateField defaults to not being required """
        self.assertEqual(self.field.required, False)

    def test_field_widget(self):
        """ Check AMPDateField uses widget AMPDateWidget """
        self.assertEqual(type(self.field.widget), AMPDateWidget)

    def test_field_widget_attrs(self):
        """ Check AMPDateField widget has no default attrs """
        self.assertEqual(self.field.widget.attrs, {})


class AMPDateRangeFormTestCase(TestCase):
    """
    Form AMPDateRangeForm tests

    Methods
    -------
    setUp()
        Sets up the test environment

    test_form_is_valid()
        Tests if form.is_valid() is true for valid dates

    test_form_fails_clean_start_date()
        Form fails if start date is invalid

    test_form_fails_clean_end_date()
        Form fails if end date is invalid
    """

    def setUp(self):
        """ Sets up the test environment with a request factory """
        self.factory: RequestFactory = RequestFactory()

    def test_form_conforms(self):
        """ Tests if form.is_valid() is true for valid dates """
        form: AMPDateRangeForm = AMPDateRangeForm(
            data={
                "start_date_0": "1",
                "start_date_1": "1",
                "start_date_2": "1900",
                "end_date_0": "1",
                "end_date_1": "1",
                "end_date_2": "2100",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_fails_clean_start_date(self):
        """ Tests if form.is_valid() is false if start date is invalid """
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
        self.assertFalse(form.is_valid())

    def test_form_fails_clean_end_date_year(self):
        """ Tests if form.is_valid() is false if end date is invalid """
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
        self.assertFalse(form.is_valid())
