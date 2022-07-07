"""Template tag for comment component"""
from typing import TypedDict

from django import template
from django.http import HttpRequest
from django.db.models import QuerySet

from ...cases.models import Case
from ..forms import SubmitCommentForm
from ..models import Comment

register = template.Library()


class CommentContextType(TypedDict):
    comments: QuerySet[Comment]
    request: HttpRequest
    case: Case
    contact_form: SubmitCommentForm


@register.inclusion_tag("comment_section.html")
def comments_app(request: HttpRequest, case: Case) -> CommentContextType:
    """Template tag for comment component.

    Args:
        request (HttpRequest): Django request object
        case_id (int): The case id of the case

    Returns:
        CommentContextType: Contains the comments, the request, and comment form
    """
    form: SubmitCommentForm = SubmitCommentForm()
    comments: QuerySet[Comment] = Comment.objects.filter(
        path=request.path, hidden=False
    ).order_by("-created_date")

    return {
        "comments": comments,
        "request": request,
        "case": case,
        "contact_form": form,
    }
