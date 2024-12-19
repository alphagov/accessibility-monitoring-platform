"""Case notes history"""

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .models import Case, CaseNoteHistory


class AMPNoteTextField(forms.CharField):
    """Textarea input field for case notes"""

    note_type: CaseNoteHistory.NoteType = CaseNoteHistory.NoteType.GENERIC

    def __init__(self, *args, **kwargs) -> None:
        if "note_type" in kwargs:
            self.note_type = kwargs["note_type"]
            del kwargs["note_type"]
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            forms.Textarea(attrs={"class": "govuk-textarea", "rows": "4"}),
        )
        super().__init__(*args, **kwargs)

    @property
    def case_note_history(self, case: Case):
        return case.case_note_history.filter(note_type=self.note_type)


def add_to_case_note_history(
    user: User, form: forms.ModelForm, note_owning_object: models.Model
) -> None:
    """
    Check update form for Case note field, if found save field contents
    in Case note history.
    """
    for field_name, field in form.fields.items():
        if isinstance(field, AMPNoteTextField):
            if (field_value := form.cleaned_data.get(field_name)) is not None:
                if form.instance is not None:
                    case: Case | None = None
                    if isinstance(form.instance, Case):
                        case = form.instance
                    elif hasattr(form.instance, "case"):
                        case = form.instance.case
                if case is not None and case.id:
                    CaseNoteHistory.objects.create(
                        case=case,
                        note_type=field.note_type,
                        note=field_value,
                        user=user,
                        created=timezone.now(),
                    )
                    setattr(note_owning_object, field_name, "")
