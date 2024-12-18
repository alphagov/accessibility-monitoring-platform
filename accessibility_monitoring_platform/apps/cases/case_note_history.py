"""Case notes history"""

from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .models import Case, CaseNoteHistory


class AMPNoteWidget(forms.TextInput):
    """Widget for Case notes input field with history"""

    template_name = "cases/case_note_history_field.html"


class AMPNoteTextField(forms.CharField):
    """
    Textarea input field in the style of GDS design system.
    Widget shows history of Case notes added using this field.
    """

    note_type: CaseNoteHistory.NoteType = CaseNoteHistory.NoteType.GENERIC

    def __init__(self, *args, **kwargs) -> None:
        if "note_type" in kwargs:
            self.note_type = kwargs["note_type"]
            del kwargs["note_type"]
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "widget",
            AMPNoteWidget(attrs={"class": "govuk-textarea", "rows": "4"}),
        )
        super().__init__(*args, **kwargs)


class CaseNoteHistoryForm(forms.ModelForm):
    """
    Form which includes Case notes field(s).
    Adds history of notes entered to widgets.
    """

    version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, AMPNoteTextField):
                if self.instance is not None:
                    case: Case | None = None
                    if isinstance(self.instance, Case):
                        case = self.instance
                    elif hasattr(self.instance, "case"):
                        case = self.instance.case
                if case is not None and case.id:
                    field.widget.attrs["field_label"] = field.label
                    field.widget.attrs["case_note_history"] = (
                        case.case_note_history.filter(note_type=field.note_type)
                    )


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
