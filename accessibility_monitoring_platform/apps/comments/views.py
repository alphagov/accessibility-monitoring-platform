"""
Views for comment app
"""

from typing import Dict, Type

from django.forms.models import ModelForm
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..common.utils import record_model_update_event
from .forms import CommentUpdateForm
from .models import Comment


class QACommentUpdateView(UpdateView):
    """
    View to update a comment
    """

    model: Type[Comment] = Comment
    form_class: Type[CommentUpdateForm] = CommentUpdateForm
    context_object_name: str = "comment"
    template_name: str = "comments/qa_update_comment.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        comment: Comment = form.save(commit=False)
        if "remove_comment" in self.request.POST:
            if comment.user.id == self.request.user.id:  # type: ignore
                comment.hidden = True
        record_model_update_event(user=self.request.user, model_object=comment)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case_pk: Dict[str, int] = {"pk": self.object.case.id}  # type: ignore
        return f"{reverse('cases:edit-qa-comments', kwargs=case_pk)}?#qa-discussion"
