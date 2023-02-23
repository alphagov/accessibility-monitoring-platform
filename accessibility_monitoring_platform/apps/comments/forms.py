"""Forms for comment box"""
from django import forms
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
