"""
Views - account_details - users
"""

from typing import TypedDict, List, Any, Dict

from django.contrib.auth import login
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

from accessibility_monitoring_platform.apps.users.forms import UpdateUserForm
from accessibility_monitoring_platform.apps.common.utils import (
    record_model_update_event,
)
from accessibility_monitoring_platform.apps.notifications.models import (
    NotificationsSettings,
)


class AccountDetailsContext(TypedDict):
    form: UpdateUserForm
    form_groups: List[str]


@login_required
def account_details(request: HttpRequest) -> HttpResponse:
    """
    Account details view

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        HttpResponse: Django HttpResponse
    """
    request_temp: Any = request
    user: User = get_object_or_404(User, id=request_temp.user.id)
    if NotificationsSettings.objects.filter(pk=user.id).exists():  # type: ignore
        notification_settings: NotificationsSettings = NotificationsSettings.objects.get(pk=user.id)  # type: ignore
    else:
        notification_settings: NotificationsSettings = NotificationsSettings(
            user=user,
            email_notifications_enabled=False,
        )
        notification_settings.save()

    initial: Dict[str, Any] = model_to_dict(user)
    initial["email_confirm"] = initial["email"]
    initial["email_notifications"] = notification_settings.email_notifications_enabled

    form: UpdateUserForm = UpdateUserForm(
        data=request.POST or None, request=request, initial=initial
    )

    if request.method == "POST":
        if form.is_valid():
            user.username = form.cleaned_data["email"]
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            record_model_update_event(user=request.user, model_object=user)  # type: ignore
            user.save()

            notification_settings.email_notifications_enabled = (
                form.cleaned_data["email_notifications"] == "yes"
            )
            notification_settings.save()

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Successfully saved details!")
            return redirect("users:account_details")
        messages.error(request, "There were errors in the form")

    context: AccountDetailsContext = {
        "form": form,
        "form_groups": ["last_name", "email_confirm"],
    }

    return render(request, "users/account_details.html", context)
