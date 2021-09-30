"""Template tag for comment component"""
from typing import TypedDict
from django import template
from django.http import HttpRequest
from django.db.models import QuerySet
from ..forms import SubmitCommentForm
from ..models import Comments

register = template.Library()


class CommentContextType(TypedDict):
    comments: QuerySet
    request: HttpRequest
    contact_form: SubmitCommentForm


@register.inclusion_tag("comment_section.html")
def comments_app(request: HttpRequest, case_id: int, page: str) -> CommentContextType:
    """Template tag for comment component. It manages the data for the
    for the component with session data.

    It's designed to use the request data for locating comments but uses case_id
    and page as a backup in case the URLs change in the future.

    Args:
        request (HttpRequest): Django request object
        case_id (int): The case id of the case
        page (str): A descriptor for the case

    Returns:
        CommentContextType: Contains the comments, the request, and comment form
    """
    request.session["comment_page"] = page
    request.session["comment_path"] = request.path
    request.session["case_id"] = case_id
    form: SubmitCommentForm = SubmitCommentForm()
    comments = Comments.objects.filter(
        path=request.path,
        hidden=False
    ).order_by(
        "-created_date"
    )
    return {
        "comments": comments,
        "request": request,
        "contact_form": form,
    }
