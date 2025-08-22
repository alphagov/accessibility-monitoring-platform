"""Comments utilities"""

from django.contrib.auth.models import Group, User
from django.http import HttpRequest

from ..cases.models import BaseCase
from ..common.models import Platform
from ..common.utils import get_platform_settings
from ..notifications.models import Task
from ..notifications.utils import add_task
from ..simplified.utils import record_simplified_model_create_event
from .models import Comment


def add_comment_notification(request: HttpRequest, comment: Comment) -> bool:
    """Will notify all users in a comment thread if they have commented"""
    user_ids: set[int] = set(
        Comment.objects.filter(base_case=comment.base_case, hidden=False).values_list(
            "user", flat=True
        )
    )

    # If commentor is not auditor, then it add auditor to list of ids
    if (
        comment.base_case is not None
        and comment.base_case.auditor is not None
        and request.user != comment.base_case.auditor
    ):
        user_ids.add(comment.base_case.auditor.id)

    # Find the QA and add them to the set of ids
    if comment.base_case and comment.base_case.reviewer:
        user_ids.add(comment.base_case.reviewer.id)

    # Add the on-call QA to the set of ids
    platform: Platform = get_platform_settings()
    if platform.active_qa_auditor:
        user_ids.add(platform.active_qa_auditor.id)

    # If a detailed case has not auditor then add all QA auditors' ids
    if (
        comment.base_case.auditor is None
        and comment.base_case.test_type == BaseCase.TestType.DETAILED
    ):
        qa_auditor_group: Group = Group.objects.get(name="QA auditor")
        for user in qa_auditor_group.user_set.all():
            user_ids.add(user.id)

    # Remove the commentor from the list of ids
    if request.user.id in user_ids:
        user_ids.remove(request.user.id)

    first_name: str = request.user.first_name
    last_name: str = request.user.last_name
    description: str = (
        f"{first_name} {last_name} left a message in discussion:\n\n{comment.body}"
    )
    organisation_name: str = (
        comment.base_case.organisation_name if comment.base_case is not None else ""
    )
    email_description: str = f"{organisation_name} | COMMENT"

    for target_user_id in user_ids:
        target_user = User.objects.get(id=target_user_id)
        task: Task = add_task(
            user=target_user,
            base_case=comment.base_case,
            type=Task.Type.QA_COMMENT,
            description=description,
            email_description=email_description,
            request=request,
        )
        if comment.base_case.test_type == BaseCase.TestType.SIMPLIFIED:
            record_simplified_model_create_event(
                user=request.user,
                model_object=task,
                simplified_case=comment.base_case.simplifiedcase,
            )
    return True
