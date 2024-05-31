"""Views for notifications app"""

from typing import Type

from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ..cases.models import Case
from ..common.utils import record_model_create_event, record_model_update_event
from .forms import ReminderForm
from .models import Task
from .utils import build_task_list


class TaskListView(TemplateView):
    """
    Lists all tasks for user
    """

    template_name: str = "notifications/task_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tasks"] = build_task_list(user=self.request.user)
        return context


class TaskMarkAsReadView(ListView):
    """
    Mark task as read
    """

    model = Task

    def get(self, request, pk):
        """Hides a task"""
        task: Task = Task.objects.get(pk=pk)
        if (
            task.user.id == request.user.id  # type: ignore
        ):  # Checks whether the task was created by user
            task.read = True
            task.save()
            if task.type == Task.Type.REMINDER:
                messages.success(request, f"{task.case} Reminder task deleted")
            else:
                messages.success(
                    request,
                    f"{task.case} {task.get_type_display()} task marked as read",
                )
        else:
            messages.error(request, "An error occured")

        return HttpResponseRedirect(reverse_lazy("notifications:task-list"))


class ReminderTaskCreateView(CreateView):
    """
    View to create reminder task
    """

    model: Type[Task] = Task
    context_object_name: str = "task"
    form_class: Type[ReminderForm] = ReminderForm
    template_name: str = "notifications/reminder_task_create.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        if form.changed_data:
            case: Case = Case.objects.get(pk=self.kwargs["case_id"])
            user: User = case.auditor if case.auditor else self.request.user
            self.object: Task = Task.objects.create(
                date=form.cleaned_data["date"],
                type=Task.Type.REMINDER,
                case=case,
                user=user,
                description=form.cleaned_data["description"],
            )
            record_model_create_event(user=self.request.user, model_object=self.object)
        return HttpResponseRedirect(
            reverse_lazy("cases:case-detail", kwargs={"pk": case.id})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case"] = Case.objects.get(pk=self.kwargs["case_id"])
        return context

    def get_success_url(self) -> str:
        """Record creation event"""
        record_model_create_event(user=self.request.user, model_object=self.object)
        return super().get_success_url()


class ReminderTaskUpdateView(UpdateView):
    """
    View to update reminder
    """

    model: Type[Task] = Task
    context_object_name: str = "task"
    form_class: Type[ReminderForm] = ReminderForm
    success_url: str = reverse_lazy("notifications:task-list")
    template_name: str = "notifications/reminder_task_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of task"""
        if form.changed_data or "delete" in self.request.POST:
            self.object: Task = form.save(commit=False)
            if "delete" in self.request.POST:
                self.object.read = True
            record_model_update_event(user=self.request.user, model_object=self.object)
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["case"] = self.object.case
        return context
