from datetime import date
from typing import Union

from .forms import CasePostReportUpdateForm
from .models import Case


def get_sent_date(
    form: CasePostReportUpdateForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: date = form.cleaned_data[sent_date_name]
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form
