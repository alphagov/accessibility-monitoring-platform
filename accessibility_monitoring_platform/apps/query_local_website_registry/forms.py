from django import forms


class SearchForm(forms.Form):
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
                'type': 'text',
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
                'type': 'text',
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
                'type': 'text',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )

    end_date_day = forms.IntegerField(
        label='Last Updated End Date',
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(
            attrs={
                'class': 'govuk-input govuk-date-input__input govuk-input--width-2',
                'type': 'text',
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
                'type': 'text',
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
                'type': 'text',
                'pattern': '[0-9]*',
                'inputmode': 'numeric',
            }
        ),
        required=False,
    )
