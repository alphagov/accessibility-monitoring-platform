from django.shortcuts import render
from django.views.generic import ListView
from django.db.models.query import QuerySet
from ..cases.models import Case
from .utils import get_overdue_cases


class OverdueView(ListView):
    """
    View of list of overdue tasks for user
    """
    template_name = "overdue/overdue_list.html"
    models = Case
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Case]:
        return get_overdue_cases(user_request=self.request.user)  # type: ignore

    def get_context_data(self, *args, **kwargs):
        context = super(OverdueView, self).get_context_data(*args, **kwargs)
        context["overdue_cases"] = get_overdue_cases(user_request=self.request.user)  # type: ignore
        return context
