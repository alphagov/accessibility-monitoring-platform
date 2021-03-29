"""
Forms - query_local_website_registry
"""

from django import forms
import datetime
from django.core.exceptions import ValidationError


class SearchForm(forms.Form):
    """
    Forms for query_local_website_registry
    """
    service = forms.CharField(
        label='Service',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'govuk-input govuk-input--width-10'}),
        required=False,
    )

    sector_name = forms.CharField(
        label='Sector Name',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'govuk-input govuk-input--width-10'}),
        required=False,
    )

    location = forms.CharField(
        label='Town/City',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'govuk-input govuk-input--width-10'}),
        required=False,
    )

    start_date_day = forms.IntegerField(
        label='Last Updated Start Date',
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-2',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    start_date_month = forms.IntegerField(
        label='Last Updated Start Date',
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-2',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    start_date_year = forms.IntegerField(
        label='Last Updated Start Date',
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-4',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    def clean_start_date_year(self):
        start_date_day_clean: str = self.cleaned_data.get('start_date_day')
        start_date_month_clean: str = self.cleaned_data.get('start_date_month')
        start_date_year_clean: str = self.cleaned_data.get('start_date_year')
        if (
            start_date_day_clean is not None
            and start_date_month_clean is not None
            and start_date_year_clean is not None
        ):
            try:
                datetime.datetime(
                    day=int(start_date_day_clean),
                    month=int(start_date_month_clean),
                    year=int(start_date_year_clean)
                )
            except Exception as e:
                raise ValidationError(
                    'This date is invalid',
                    code='email_is_not_permitted',
                ) from e
        return self.cleaned_data.get('start_date_year')

    end_date_day = forms.IntegerField(
        label='Last Updated End Date',
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-2',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    end_date_month = forms.IntegerField(
        label='Last Updated End Date',
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-2',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    end_date_year = forms.IntegerField(
        label='Last Updated End Date',
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-4',
                'type': 'number',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    def clean_end_date_year(self):
        end_date_day_clean: str = self.cleaned_data.get('end_date_day')
        end_date_month_clean: str = self.cleaned_data.get('end_date_month')
        end_date_year_clean: str = self.cleaned_data.get('end_date_year')
        if (
            end_date_day_clean is not None
            and end_date_month_clean is not None
            and end_date_year_clean is not None
        ):
            try:
                datetime.datetime(
                    day=int(end_date_day_clean),
                    month=int(end_date_month_clean),
                    year=int(end_date_year_clean)
                )
            except Exception as e:
                raise ValidationError(
                    'This date is invalid',
                    code='email_is_not_permitted',
                ) from e
        return self.cleaned_data.get('end_date_year')
