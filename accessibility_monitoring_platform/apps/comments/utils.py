""" Comments utilities """

from django.contrib.auth.models import User
from django.http import HttpRequest

from ..common.models import Platform
from ..common.utils import get_platform_settings, record_model_create_event
from ..notifications.models import Task
from ..notifications.utils import add_task
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
    user_ids: set[int] = set(
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
    description: str = (
        f"{first_name} {last_name} left a message in discussion:\n\n{comment.body}"
    )
    organisation_name: str = (
        comment.case.organisation_name if comment.case is not None else ""
    )
    list_description: str = f"{organisation_name} | COMMENT"

    for target_user_id in user_ids:
        target_user = User.objects.get(id=target_user_id)
        task: Task = add_task(
            user=target_user,
            case=comment.case,
            type=Task.Type.QA_COMMENT,
            description=description,
            list_description=list_description,
            request=request,
        )
        record_model_create_event(user=request.user, model_object=task)
    return True
