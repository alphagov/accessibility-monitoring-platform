"""Forms for comment box"""
from typing import List
from django import forms
from django.core.exceptions import ValidationError
from ..common.forms import AMPTextField
from .models import Comment


class CommentCreateForm(forms.ModelForm):
    """
    Form for creating a comment
    """

    body: AMPTextField = AMPTextField(label="Add comment")

    class Meta:
        model = Comment
        fields = ["body"]


class CommentUpdateForm(forms.ModelForm):
    """
    Form for updating a comment
    """

    body: AMPTextField = AMPTextField(label="Edit comment")

    class Meta:
        model = Comment
        fields = ["body"]


class SubmitCommentForm(forms.ModelForm):
    """
    Form for creating a comment
    """

    body: AMPTextField = AMPTextField(label="Enter your comment")

    class Meta:
        model = Comment
        fields = ["body"]


class EditCommentForm(forms.ModelForm):
    """
    Form for creating a case
    """

    body: AMPTextField = AMPTextField(label="Enter your comment")

    class Meta:
        model = Comment
        fields: List[str] = ["body"]

    def clean_body(self) -> str:
        body: str = self.cleaned_data.get("body", "")
        if self.initial["request"].user.id != self.instance.user.id:
            raise ValidationError("A problem occured. Please contact an admin.")
        return body
