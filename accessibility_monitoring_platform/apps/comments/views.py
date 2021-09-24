""" Comments view - handles posting and editing comments """
from typing import Union
from datetime import datetime
from django.utils import timezone
from django.views.generic.edit import FormView, View, UpdateView
from django.forms.models import ModelForm
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpRequest
from accessibility_monitoring_platform.apps.cases.models import Case
from .models import Comments, CommentsHistory
from .forms import SubmitCommentForm, EditCommentForm


def save_comment_history(obj: Comments) -> bool:
    """Will take a new comment object and save the history to comment history"""
    original_comment = Comments.objects.get(pk=obj.id)
    history = CommentsHistory(
        comment=obj,
        before=getattr(original_comment, "body"),
        after=obj.body
    )
    history.save()
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
        obj.endpoint = self.request.session.get("comment_endpoint")
        if self.request.session.get("case_id"):
            obj.case = Case.objects.get(pk=self.request.session.get("case_id"))
        obj.save()

        endpoint: Union[str, None] = self.request.session.get("comment_endpoint")
        if endpoint:
            return HttpResponseRedirect(endpoint)
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

        endpoint: Union[str, None] = self.request.session.get("comment_endpoint")
        if endpoint:
            return HttpResponseRedirect(endpoint)
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
        endpoint: Union[str, None] = self.request.session.get("comment_endpoint")
        if endpoint:
            return HttpResponseRedirect(endpoint)
        return HttpResponseRedirect("/")
