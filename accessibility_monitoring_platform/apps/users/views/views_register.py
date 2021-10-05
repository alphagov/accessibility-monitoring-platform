"""
Views - register - users
"""

from typing import TypedDict, List
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from accessibility_monitoring_platform.apps.users.forms import CustomUserCreationForm
from accessibility_monitoring_platform.apps.notifications.models import NotificationsSettings


class RegisterContext(TypedDict):
    form: CustomUserCreationForm
    form_groups: List[str]


def register(request: HttpRequest) -> HttpResponse:
    """
    Register view

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        HttpResponse: Django HttpResponse
    """
    if request and request.user and request.user.is_authenticated:
        return redirect(reverse("dashboard:home"))

    form: CustomUserCreationForm = CustomUserCreationForm(
        data=request.POST or None, request=request
    )

    if request.method == "POST":
        if form.is_valid():
            user: User = form.save()
            user.username = form.cleaned_data["email"]
            user.save()
            NotificationsSettings(user=user).save()
            login(request, user)
            return redirect(reverse("dashboard:home"))

    context: RegisterContext = {
        "form": form,
        "form_groups": ["last_name", "email_confirm"],
    }

    return render(request, "users/register.html", context)
