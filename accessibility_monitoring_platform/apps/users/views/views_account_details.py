"""
Views - account_details - users
"""

from typing import TypedDict, List, Any
from django.contrib.auth import login
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from accessibility_monitoring_platform.apps.users.forms import UpdateUserForm
# from accessibility_monitoring_platform.apps.notifications.models import NotificationsSettings
from accessibility_monitoring_platform.apps.users.models import Auditor


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
    # notification_settings = NotificationsSettings.objects.get(user=user)
    try:
        auditor = Auditor.objects.get(user=user)
    except Auditor.DoesNotExist:
        auditor = Auditor.objects.create(user=user)

    initial = model_to_dict(user)
    initial["email_confirm"] = initial["email"]
    # initial["email_notifications"] = notification_settings.email_notifications_enabled
    initial["active_qa_auditor"] = auditor.active_qa_auditor

    form: UpdateUserForm = UpdateUserForm(
        data=request.POST or None, request=request, initial=initial
    )

    if request.method == "POST":
        if form.is_valid():
            user.username = form.cleaned_data["email"]
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()

            # notification_settings.email_notifications_enabled = (form.cleaned_data["email_notifications"] == "yes")
            # notification_settings.save()
            auditor.active_qa_auditor = (form.cleaned_data["active_qa_auditor"] == "yes")
            auditor.save()

            login(request, user)
            messages.success(request, "Successfully saved details!")
            return redirect("users:account_details")
        messages.error(request, "There were errors in the form")

    context: AccountDetailsContext = {
        "form": form,
        "form_groups": ["last_name", "email_confirm"],
        "is_qa_auditor": user.groups.filter(name="QA auditor").exists(),
    }

    return render(request, "users/account_details.html", context)
