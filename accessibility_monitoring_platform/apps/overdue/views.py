"""View for overdue"""
from django.db.models.query import QuerySet
from django.views.generic import ListView

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
