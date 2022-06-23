"""
Views - users
"""
from typing import Type

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView

from ..common.utils import record_model_create_event, record_model_update_event
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

    def form_valid(self, form: UserCreateForm):
        """Process contents of valid form"""
        user: User = form.save(commit=False)
        user.username = form.cleaned_data["email"]
        user.save()

        NotificationSetting.objects.create(user=user)

        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return HttpResponseRedirect("/")

    def get_success_url(self) -> str:
        record_model_create_event(user=self.request.user, model_object=self.object)  # type: ignore
        return reverse("dashboard:home")


class UserUpdateView(UpdateView):
    """
    View to update a user
    """

    model: Type[User] = User
    form_class: Type[UserUpdateForm] = UserUpdateForm
    context_object_name: str = "user"
    template_name: str = "users/forms/update.html"

    def get_success_url(self) -> str:
        record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
        return reverse("dashboard:home")
