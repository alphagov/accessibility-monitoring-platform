""" Comments view - handles posting and editing comments """
from typing import Union, List, Any
from datetime import datetime
from django.utils import timezone
from django.db.models import QuerySet
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import View
from django.forms.models import ModelForm
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpRequest
from django.contrib.auth.models import User
from accessibility_monitoring_platform.apps.cases.models import Case
from .models import Comments, CommentsHistory
from .forms import SubmitCommentForm, EditCommentForm
from ..notifications.add_notification import add_notification


def save_comment_history(obj: Comments) -> bool:
    """Will take a new comment object and save the history to comment history"""
    original_comment: Comments = Comments.objects.get(pk=obj.id)
    history: CommentsHistory = CommentsHistory(
        comment=obj,
        before=getattr(original_comment, "body"),
        after=obj.body
    )
    history.save()
    return True


def add_comment_notification(request: HttpRequest, obj: Comments) -> bool:
    """ Will notify all users in a comment thread if they have commented. Will also notify the QA auditor if
    the comment section is in "edit-report-details"

    Parameters
    ----------
    request : HttpRequest
        Django request
    obj : Comments
        Comments object

    Returns
    -------
    bool
        Returns true if function is successful
    """
    users_on_thread: QuerySet = Comments.objects.filter(
        path=request.session.get("comment_path"),
        hidden=False,
    ).values_list(
        "user",
        flat=True
    ).distinct()

    users_on_thread_list: List[Any] = list(users_on_thread)
    users_on_thread_list_int: List[int] = [int(x) for x in users_on_thread_list]

    # If commentor is not auditor, then it add auditor to list of ids
    if obj.case.auditor and request.user != obj.case.auditor:
        users_on_thread_list_int.append(obj.case.auditor.id)

    # If page is edit-report-details, then it finds the QA and adds them to the list of ids
    if (
        obj.case
        and obj.case.reviewer
        and request.session.get("comment_path")
        and "edit-report-details" in str(request.session.get("comment_path"))
    ):
        users_on_thread_list_int.append(obj.case.reviewer.id)

    unique_values = list(set(users_on_thread_list_int))  # Gets the unique user ids

    # Removes the commentor from the list of ids
    if request.user.id in unique_values:
        unique_values.remove(request.user.id)

    for target_user_id in unique_values:
        target_user = User.objects.get(id=target_user_id)
        add_notification(
            user=target_user,
            body=f"{request.user.first_name} {request.user.last_name} left a message in discussion",
            path=str(request.session.get("comment_path")),
            list_description=f"{obj.case.organisation_name} | {obj.page.replace('_', ' ').capitalize() }",
            request=request,
        )
    return True


class CommentsPostView(FormView):
    """
    Post comment
    """
    form_class = SubmitCommentForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Process contents of valid form"""
        form = SubmitCommentForm(self.request.POST)
        obj: Comments = form.save(commit=False)

        obj.user = self.request.user
        obj.page = self.request.session.get("comment_page")
        obj.path = self.request.session.get("comment_path")
        if self.request.session.get("case_id"):
            obj.case = Case.objects.get(pk=self.request.session.get("case_id"))
        obj.save()

        add_comment_notification(self.request, obj)

        path: Union[str, None] = self.request.session.get("comment_path")
        if path:
            return HttpResponseRedirect(f"{path}#comments")
        return HttpResponseRedirect("/")


class CommentDeleteView(View):
    """Post view for deleting a comment"""
    model = Comments

    def post(self, request: HttpRequest, pk: int) -> HttpResponseRedirect:
        """ Deletes a comment """
        comments: Comments = Comments.objects.get(pk=pk)
        if comments.user.id == request.user.id:  #Checks whether the comment was posted by user
            comments.hidden = True
            comments.save()
            messages.success(request, "Comment successfully removed")
        else:
            messages.error(request, "An error occured")

        path: Union[str, None] = self.request.session.get("comment_path")
        if path:
            return HttpResponseRedirect(path)
        return HttpResponseRedirect("/")


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
        obj: Comments = form.save(commit=False)
        obj.updated_date = datetime.now(tz=timezone.utc)

        save_comment_history(obj)
        obj.save()

        messages.success(self.request, "Comment succesfully updated")
        path: Union[str, None] = self.request.session.get("comment_path")
        if path:
            return HttpResponseRedirect(path)
        return HttpResponseRedirect("/")
