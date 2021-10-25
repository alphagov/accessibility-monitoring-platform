"""
Views for checks app (called tests by users)
"""
from typing import List, Type

from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import CheckCreateForm
from .models import Check


class CheckCreateView(CreateView):
    """
    View to create a check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"
    form_class: Type[CheckCreateForm] = CheckCreateForm
    template_name: str = "checks/create_form.html"

class CheckDetailView(DetailView):
    """
    View of details of a single check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"


class CheckUpdateView(UpdateView):
    """
    View to update check
    """

    model: Type[Check] = Check
    context_object_name: str = "check"


class CheckListView(ListView):
    """
    View of list of checks
    """

    model: Type[Check] = Check
    context_object_name: str = "checks"
    paginate_by: int = 10
