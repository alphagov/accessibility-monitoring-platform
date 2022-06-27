"""Forms for comment box"""
from typing import List
from django import forms
from django.core.exceptions import ValidationError
from ..common.forms import AMPTextField
from .models import Comments


class SubmitCommentForm(forms.ModelForm):
    """
    Form for creating a case
    """

    body: AMPTextField = AMPTextField(label="Enter your comment")

    class Meta:
        model = Comments
        fields = ["body"]


class EditCommentForm(forms.ModelForm):
    """
    Form for creating a case
    """

    body: AMPTextField = AMPTextField(label="Enter your comment")

    class Meta:
        model = Comments
        fields: List[str] = ["body"]

    def clean_body(self) -> str:
        body: str = self.cleaned_data.get("body", "")
        if self.initial["request"].user.id != self.instance.user.id:
            raise ValidationError("A problem occured. Please contact an admin.")
        return body
