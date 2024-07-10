"""Views for notifications app"""

from typing import Dict, List, Type

from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ..cases.models import Case
from ..common.utils import record_model_create_event, record_model_update_event
from .forms import ReminderForm
from .models import Task
from .utils import (
    TASK_LIST_PARAMS,
    build_task_list,
    get_task_type_counts,
    mark_tasks_as_read,
)


class TaskListView(TemplateView):
    """
    Lists all tasks for user
    """

    template_name: str = "notifications/task_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params: Dict[str, str] = {
            param: self.request.GET.get(param) for param in TASK_LIST_PARAMS
        }
        user: User = self.request.user

        # Check for parameter to list another user's Tasks. Usefult for live support.
        if "user_id" in self.request.GET:
            user_id: str = self.request.GET.get("user_id")
            if user_id.isnumeric():
                try:
                    user: User = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass

        context["tasks"] = build_task_list(user=user, **params)
        all_due_tasks: List[Task] = build_task_list(user=user)
        context["task_type_counts"] = get_task_type_counts(tasks=all_due_tasks)
        return {**context, **params}


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


class CommentsMarkAsReadView(ListView):
    """
    Mark all QA comment and report approves tasks as read
    """

    model = Task

    def get(self, request, case_id):
        """Hides a task"""
        case: Case = Case.objects.get(id=case_id)
        mark_tasks_as_read(user=self.request.user, case=case, type=Task.Type.QA_COMMENT)
        mark_tasks_as_read(
            user=self.request.user, case=case, type=Task.Type.REPORT_APPROVED
        )
        messages.success(request, f"{case} comments marked as read")
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
        return reverse("cases:case-detail", kwargs={"pk": self.object.case.id})


class ReminderTaskUpdateView(UpdateView):
    """
    View to update reminder
    """

    model: Type[Task] = Task
    context_object_name: str = "task"
    form_class: Type[ReminderForm] = ReminderForm
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

    def get_success_url(self) -> str:
        """Record creation event"""
        return reverse("cases:case-detail", kwargs={"pk": self.object.case.id})
