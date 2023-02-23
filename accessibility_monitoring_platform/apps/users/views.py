"""
Views - users
"""
from typing import Type

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView

from django_otp.plugins.otp_email.models import EmailDevice

from ..common.models import (
    BOOLEAN_FALSE,
    BOOLEAN_TRUE,
)
from ..common.utils import (
    checks_if_2fa_is_enabled,
    record_model_create_event,
    record_model_update_event,
)
from ..notifications.models import NotificationSetting

from .forms import UserCreateForm, UserUpdateForm


class UserCreateView(CreateView):
    """
    View to create/register a user
    """

    model: Type[User] = User
    form_class: Type[UserCreateForm] = UserCreateForm
    context_object_name: str = "user"
    template_name: str = "users/forms/create.html"

    def get(self, *args, **kwargs):
        """Redirect tp dashboard if already logged in"""
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse("dashboard:home"))
        return super().get(*args, **kwargs)

    def form_valid(self, form: UserCreateForm):
        """Process contents of valid form"""
        user: User = form.save(commit=False)
        user.username = form.cleaned_data["email"]
        user.save()

        NotificationSetting.objects.create(user=user)

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        record_model_create_event(user=self.request.user, model_object=user)
        return HttpResponseRedirect(reverse("dashboard:home"))


class UserUpdateView(UpdateView):
    """
    View to update a user
    """

    model: Type[User] = User
    form_class: Type[UserUpdateForm] = UserUpdateForm
    context_object_name: str = "user"
    template_name: str = "users/forms/update.html"

    def get_form_kwargs(self):
        """Pass user to form"""
        kwargs = super().get_form_kwargs()
        user: User = self.object
        kwargs.update({"user": user})
        return kwargs

    def get_form(self):
        """Populate enable_2fs and email_notifications fields"""
        form = super().get_form()
        user: User = self.object
        if checks_if_2fa_is_enabled(user=user):
            form.fields["enable_2fa"].initial = BOOLEAN_TRUE
        else:
            form.fields["enable_2fa"].initial = BOOLEAN_FALSE
        notification_setting, _ = NotificationSetting.objects.get_or_create(user=user)
        form.fields[
            "email_notifications"
        ].initial = notification_setting.email_notifications_enabled
        return form

    def form_valid(self, form: UserUpdateForm):
        """Process contents of valid form"""
        user: User = User.objects.get(
            id=self.object.id
        )  # Ignore password field in form

        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        record_model_update_event(user=self.request.user, model_object=user)
        user.save()

        notification_setting: NotificationSetting = NotificationSetting.objects.get(
            user=user
        )
        notification_setting.email_notifications_enabled = (
            form.cleaned_data["email_notifications"] == "yes"
        )
        notification_setting.save()

        enable_2fa: str = form.cleaned_data.get("enable_2fa", "")
        email_device, _ = EmailDevice.objects.get_or_create(user=user, name="default")
        email_device.confirmed = enable_2fa == BOOLEAN_TRUE
        email_device.save()

        messages.success(self.request, "Successfully saved details!")
        return HttpResponseRedirect(reverse("users:edit-user", kwargs={"pk": user.id}))
