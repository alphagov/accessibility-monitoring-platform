""" Comments utilities """
from typing import Set

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse

from ..common.models import Platform
from ..common.utils import get_platform_settings
from ..notifications.utils import add_notification
from .models import Comment


def add_comment_notification(request: HttpRequest, comment: Comment) -> bool:
    """
    Will notify all users in a comment thread if they have commented.

    Parameters
    ----------
    request : HttpRequest
        Django request
    comment : Comment
        Comment object

    Returns
    -------
    bool
        Returns true if function is successful
    """
    user_ids: Set[int] = set(
        Comment.objects.filter(case=comment.case, hidden=False).values_list(
            "user", flat=True
        )
    )

    # If commentor is not auditor, then it add auditor to list of ids
    if (
        comment.case is not None
        and comment.case.auditor is not None
        and request.user != comment.case.auditor
    ):
        user_ids.add(comment.case.auditor.id)

    # Find the QA and add them to the set of ids
    if comment.case and comment.case.reviewer:
        user_ids.add(comment.case.reviewer.id)

    # Add the on-call QA to the set of ids
    platform: Platform = get_platform_settings()
    if platform.active_qa_auditor:
        user_ids.add(platform.active_qa_auditor.id)

    # Remove the commentor from the list of ids
    if request.user.id in user_ids:
        user_ids.remove(request.user.id)

    first_name: str = request.user.first_name
    last_name: str = request.user.last_name
    body: str = (
        f"{first_name} {last_name} left a message in discussion:\n\n{comment.body}"
    )
    organisation_name: str = (
        comment.case.organisation_name if comment.case is not None else ""
    )
    list_description: str = f"{organisation_name} | COMMENT"

    for target_user_id in user_ids:
        target_user = User.objects.get(id=target_user_id)
        add_notification(
            user=target_user,
            body=body,
            path=reverse("cases:edit-qa-process", kwargs={"pk": comment.case.id}),  # type: ignore
            list_description=list_description,
            request=request,
        )
    return True
