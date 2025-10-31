"""
Views for comment app
"""

from django.forms.models import ModelForm
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..cases.models import BaseCase
from ..simplified.utils import record_simplified_model_update_event
from .forms import CommentUpdateForm
from .models import Comment


class QACommentUpdateView(UpdateView):
    """
    View to update a comment
    """

    model: type[Comment] = Comment
    form_class: type[CommentUpdateForm] = CommentUpdateForm
    context_object_name: str = "comment"
    template_name: str = "comments/qa_update_comment.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        comment: Comment = form.save(commit=False)
        if "remove_comment" in self.request.POST:
            if comment.user.id == self.request.user.id:  # type: ignore
                comment.hidden = True
        if comment.base_case.test_type == BaseCase.TestType.SIMPLIFIED:
            record_simplified_model_update_event(
                user=self.request.user,
                model_object=comment,
                simplified_case=comment.base_case.simplifiedcase,
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case_pk: dict[str, int] = {"pk": self.object.base_case.id}  # type: ignore
        url_name: str = f"{self.object.base_case.test_type}:edit-qa-comments"
        return f"{reverse(url_name, kwargs=case_pk)}?#qa-discussion"
