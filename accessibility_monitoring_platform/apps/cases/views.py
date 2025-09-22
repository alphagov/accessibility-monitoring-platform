"""
Views for cases app
"""

from typing import Any

from django.db.models.query import QuerySet
from django.views.generic.list import ListView

from ..common.utils import (
    check_dict_for_truthy_values,
    get_dict_without_page_items,
    get_url_parameters_for_pagination,
    replace_search_key_with_case_search,
)
from .forms import CaseSearchForm
from .models import BaseCase
from .utils import filter_cases

TRUTHY_SEARCH_FIELDS: list[str] = [
    "sort_by",
    "status",
    "case_number",
    "recommendation_for_enforcement",
    "auditor",
    "reviewer",
    "date_start_0",
    "date_start_1",
    "date_start_2",
    "date_end_0",
    "date_end_1",
    "date_end_2",
    "sector",
    "is_complaint",
    "enforcement_body",
    "subcategory",
    "test_type",
]


class CaseListView(ListView):
    """
    View of list of cases
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "cases"
    paginate_by: int = 10
    template_name: str = "cases/basecase_list.html"

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.form: CaseSearchForm = CaseSearchForm(
                replace_search_key_with_case_search(self.request.GET)
            )
            self.form.is_valid()
        else:
            self.form = CaseSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[BaseCase]:
        """Add filters to queryset"""
        if self.form.errors:
            return BaseCase.objects.none()

        return filter_cases(self.form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        context["advanced_search_open"] = check_dict_for_truthy_values(
            dictionary=get_dict_without_page_items(self.request.GET.items()),
            keys_to_check=TRUTHY_SEARCH_FIELDS,
        )
        context["form"] = self.form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context
