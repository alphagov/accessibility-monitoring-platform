""" Comments view - handles posting and editing comments """
from typing import Set
import datetime

from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect, HttpRequest
from django.urls import reverse
from django.views.generic import View
from django.views.generic.edit import FormView, UpdateView

from ..cases.models import Case
from ..notifications.utils import add_notification

from .forms import SubmitCommentForm, EditCommentForm
from .models import Comments, CommentsHistory


def save_comment_history(comment: Comments) -> bool:
    """Will take a new comment object and save the history to comment history"""
    original_comment: Comments = Comments.objects.get(pk=comment.id)  # type: ignore
    history: CommentsHistory = CommentsHistory(
        comment=comment, before=original_comment.body, after=comment.body
    )
    history.save()
    return True


def add_comment_notification(request: HttpRequest, comment: Comments) -> bool:
    """
    Will notify all users in a comment thread if they have commented. Will also notify the QA auditor if
    the comment section is in "edit-report-details"

    Parameters
    ----------
    request : HttpRequest
        Django request
    comment : Comments
        Comments object

    Returns
    -------
    bool
        Returns true if function is successful
    """
    user_ids: Set[int] = set(
        Comments.objects.filter(path=comment.path, hidden=False).values_list(
            "user", flat=True
        )
    )

    # If commentor is not auditor, then it add auditor to list of ids
    if comment.case.auditor and request.user != comment.case.auditor:
        user_ids.add(comment.case.auditor.id)

    # If page is edit-qa-process, then it find the QA and add them to the set of ids
    if (
        comment.case
        and comment.case.reviewer
        and "edit-qa-process" in str(comment.path)
    ):
        user_ids.add(comment.case.reviewer.id)

    # Remove the commentor from the list of ids
    if request.user.id in user_ids:  # type: ignore
        user_ids.remove(request.user.id)  # type: ignore

    first_name: str = request.user.first_name  # type: ignore
    last_name: str = request.user.last_name  # type: ignore
    body: str = (
        f"{first_name} {last_name} left a message in discussion:\n\n{comment.body}"
    )
    list_description: str = f"{comment.case.organisation_name} | {comment.page.replace('_', ' ').capitalize() }"

    for target_user_id in user_ids:
        target_user = User.objects.get(id=target_user_id)
        add_notification(
            user=target_user,
            body=body,
            path=comment.path,
            list_description=list_description,
            request=request,
        )
    return True


class CreateCaseCommentFormView(FormView):
    """
    Create comment for case
    """

    form_class = SubmitCommentForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Process contents of valid form"""
        case_id: int = self.kwargs.get("case_id")
        case: Case = Case.objects.get(id=case_id)
        comment_path: str = reverse("cases:edit-qa-process", kwargs={"pk": case_id})

        form = SubmitCommentForm(self.request.POST)
        comment: Comments = form.save(commit=False)

        comment.user = self.request.user
        comment.page = "qa_process"
        comment.case = case
        comment.path = comment_path
        comment.save()

        add_comment_notification(self.request, comment)

        return HttpResponseRedirect(f"{comment_path}#comments")


class CommentDeleteView(View):
    """Post view for deleting a comment"""

    model = Comments

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        """Deletes a comment"""
        comment: Comments = Comments.objects.get(pk=pk)
        if comment.user.id == request.user.id:  # type: ignore # Checks whether the comment was posted by user
            comment.hidden = True
            comment.save()
            messages.success(request, "Comment successfully removed")
        else:
            messages.error(request, "An error occured")

        return HttpResponseRedirect(comment.path)


class CommentEditView(UpdateView):
    """
    View to record final decision details
    """

    model = Comments
    form_class = EditCommentForm
    template_name: str = "edit_comment.html"
    context_object_name: str = "comment"

    def get_initial(self):
        init = super(CommentEditView, self).get_initial()
        init.update({"request": self.request})
        return init

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Updates comment and saves comment history"""
        form.instance.created_by = self.model.user
        comment: Comments = form.save(commit=False)
        comment.updated_date = datetime.datetime.now(tz=datetime.timezone.utc)

        save_comment_history(comment)
        comment.save()

        messages.success(self.request, "Comment succesfully updated")
        return HttpResponseRedirect(comment.path)
