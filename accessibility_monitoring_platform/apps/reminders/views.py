"""
Views for audits app (called tests by users)
"""
from typing import Type

from django.forms.models import ModelForm
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import Case
from ..common.utils import (
    record_model_update_event,
    record_model_create_event,
)

from .forms import ReminderForm
from .models import Reminder
from .utils import add_reminder_context_data


class ReminderCreateView(CreateView):
    """
    View to create a reminder
    """

    model: Type[Reminder] = Reminder
    context_object_name: str = "reminder"
    form_class: Type[ReminderForm] = ReminderForm

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        reminder: Reminder = form.save(commit=False)
        case: Case = Case.objects.get(pk=self.kwargs["case_id"])
        reminder.case = case
        reminder.user = case.auditor
        if "delete" in self.request.POST:
            reminder.is_deleted = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        return add_reminder_context_data(
            context=super().get_context_data(**kwargs),
            case_id=self.kwargs["case_id"],
        )

    def get_success_url(self) -> str:
        """Record creation eventthe submit button used and act accordingly"""
        record_model_create_event(user=self.request.user, model_object=self.object)  # type: ignore
        return super().get_success_url()


class ReminderUpdateView(UpdateView):
    """
    View to update reminder
    """

    model: Type[Reminder] = Reminder
    context_object_name: str = "reminder"
    form_class: Type[ReminderForm] = ReminderForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of reminder"""
        if form.changed_data or "delete" in self.request.POST:
            self.object: Reminder = form.save(commit=False)
            if "delete" in self.request.POST:
                self.object.is_deleted = True
            record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        return add_reminder_context_data(
            context=super().get_context_data(**kwargs),
            case_id=self.object.case.id,
        )


class ReminderListView(ListView):
    """
    View of list of for user
    """

    model: Type[Reminder] = Reminder
    context_object_name: str = "reminders"

    def get_queryset(self) -> QuerySet[Case]:
        """Get undeleted reminders for logged in user"""
        return Reminder.objects.filter(
            user=self.request.user, is_deleted=False
        ).order_by("due_date")


def delete_reminder(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Delete reminder

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of reminder to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    reminder: Reminder = get_object_or_404(Reminder, id=pk)
    reminder.is_deleted = True
    record_model_update_event(user=request.user, model_object=reminder)  # type: ignore
    reminder.save()
    return redirect(reverse("reminders:reminder-list"))
