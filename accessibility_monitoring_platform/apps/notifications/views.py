"""Views for notifications app"""

from typing import Any

from django.contrib import messages
from django.contrib.auth.models import User
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView

from ..cases.models import BaseCase
from ..simplified.models import SimplifiedCase
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)

        params: dict[str, str] = {
            param: self.request.GET.get(param) for param in TASK_LIST_PARAMS
        }

        if "show_all_users" in self.request.GET:
            tasks: list[Task] = build_task_list(user=None, **params)
            context["show_all_users"] = True
            context["tasks"] = tasks
            context["task_type_counts"] = get_task_type_counts(tasks=tasks)
            return context

        user: User = self.request.user

        # Check for parameter to list another user's Tasks. Useful for live support.
        if "user_id" in self.request.GET:
            user_id: str = self.request.GET.get("user_id")
            if user_id.isnumeric():
                try:
                    user: User = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass

        context["tasks"] = build_task_list(user=user, **params)
        all_due_tasks: list[Task] = build_task_list(user=user)
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
                messages.success(request, f"{task.base_case} Reminder task deleted")
            else:
                messages.success(
                    request,
                    f"{task.base_case} {task.get_type_display()} task marked as read",
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
        simplified_case: SimplifiedCase = SimplifiedCase.objects.get(id=case_id)
        mark_tasks_as_read(
            user=self.request.user, base_case=simplified_case, type=Task.Type.QA_COMMENT
        )
        mark_tasks_as_read(
            user=self.request.user,
            base_case=simplified_case,
            type=Task.Type.REPORT_APPROVED,
        )
        messages.success(request, f"{simplified_case} comments marked as read")
        return HttpResponseRedirect(reverse_lazy("notifications:task-list"))


class ReminderTaskCreateView(CreateView):
    """
    View to create reminder task
    """

    model: type[Task] = Task
    context_object_name: str = "task"
    form_class: type[ReminderForm] = ReminderForm
    template_name: str = "notifications/reminder_task_create.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        if form.changed_data:
            base_case: BaseCase = BaseCase.objects.get(pk=self.kwargs["case_id"])
            user: User = base_case.auditor if base_case.auditor else self.request.user
            try:
                reminder_task: Task = Task.objects.get(
                    base_case=base_case, type=Task.Type.REMINDER, read=False
                )
                reminder_task.date = form.cleaned_data["date"]
                reminder_task.user = user
                reminder_task.description = form.cleaned_data["description"]
                if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
                    record_simplified_model_update_event(
                        user=self.request.user,
                        model_object=reminder_task,
                        simplified_case=base_case.simplifiedcase,
                    )
                reminder_task.save()
            except Task.DoesNotExist:
                self.object: Task = Task.objects.create(
                    date=form.cleaned_data["date"],
                    type=Task.Type.REMINDER,
                    base_case=base_case,
                    user=user,
                    description=form.cleaned_data["description"],
                )
                if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
                    record_simplified_model_create_event(
                        user=self.request.user,
                        model_object=self.object,
                        simplified_case=base_case.simplifiedcase,
                    )
        return HttpResponseRedirect(base_case.get_absolute_url())

    def get_success_url(self) -> str:
        """Record creation event"""
        base_case: BaseCase = self.object.base_case
        if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
            record_simplified_model_create_event(
                user=self.request.user,
                model_object=self.object,
                simplified_case=base_case.simplifiedcase,
            )
        return self.object.base_case.get_absolute_url()


class ReminderTaskUpdateView(UpdateView):
    """
    View to update reminder
    """

    model: type[Task] = Task
    context_object_name: str = "task"
    form_class: type[ReminderForm] = ReminderForm
    template_name: str = "notifications/reminder_task_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add event on change of task"""
        if form.changed_data or "delete" in self.request.POST:
            self.object: Task = form.save(commit=False)
            if "delete" in self.request.POST:
                self.object.read = True
            base_case: BaseCase = self.object.base_case
            self.object.user = (
                base_case.auditor if base_case.auditor else self.request.user
            )
            if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
                record_simplified_model_update_event(
                    user=self.request.user,
                    model_object=self.object,
                    simplified_case=self.object.base_case.simplifiedcase,
                )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Redirect to reminder create page if current reminder deleted"""
        if "delete" in self.request.POST:
            return reverse(
                "notifications:reminder-create",
                kwargs={"case_id": self.object.base_case.id},
            )
        return reverse(
            "notifications:edit-reminder-task", kwargs={"pk": self.object.id}
        )
