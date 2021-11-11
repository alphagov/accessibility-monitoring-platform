"""
Views for audits app (called tests by users)
"""
from typing import Type

from django.forms.models import ModelForm
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import Case
from ..common.utils import (
    record_model_update_event,
    record_model_create_event,
)

from .forms import ReminderForm
from .models import Reminder


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
        context = super().get_context_data(**kwargs)
        context["case"] = Case.objects.get(pk=self.kwargs["case_id"])
        context["page_heading"] = "Edit case | Reminder"
        context["page_title"] = f'{context["case"].organisation_name} | {context["page_heading"]}'
        return context

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
        if form.changed_data:
            self.object: Reminder = form.save(commit=False)
            record_model_update_event(user=self.request.user, model_object=self.object)  # type: ignore
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case"] = self.object.case
        return context


class ReminderListView(ListView):
    """
    View of list of for user
    """

    model: Type[Reminder] = Reminder
    context_object_name: str = "reminders"

    def get_queryset(self) -> QuerySet[Case]:
        """Get undeleted reminders for logged in user"""
        return Reminder.objects.filter(user=self.request.user, is_deleted=False)
