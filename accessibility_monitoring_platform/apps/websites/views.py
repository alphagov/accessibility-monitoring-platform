"""
Views - websites app
"""
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
)
import urllib

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.views.generic.list import ListView

from ..common.utils import build_filters, download_as_csv
from .models import NutsConversion, WebsiteRegister
from .forms import DEFAULT_SORT, WebsiteSearchForm
from .utils import get_list_of_nuts318_codes


WEBSITE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("service", "service__icontains"),
    ("sector", "sector_id"),
    ("start_date", "last_updated__gte"),
    ("end_date", "last_updated__lte"),
]
WEBSITE_FIELDS_TO_EXPORT: List[str] = [
    "website_id",
    "url",
    "service",
    "htmlhead_title",
    "htmlmeta_description",
    "last_updated",
    "sector",
    "original_domain",
    "nuts3",
    "requires_authentication",
    "holding_page",
]


class WebsiteListView(ListView):
    """
    View of list of cases
    """

    model: WebsiteRegister = WebsiteRegister
    context_object_name: str = "websites"
    paginate_by: int = 25

    def get(self, request, *args, **kwargs):
        """ Populate filter form """
        if self.request.GET:
            self.form: WebsiteSearchForm = WebsiteSearchForm(self.request.GET)
            self.form.is_valid()
        else:
            self.form = WebsiteSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[WebsiteRegister]:
        """ Add filters to queryset """
        if not self.request.GET or self.form.errors:
            return WebsiteRegister.objects.none()

        filters: Dict[str, Any] = build_filters(
            cleaned_data=self.form.cleaned_data,
            field_and_filter_names=WEBSITE_FIELD_AND_FILTER_NAMES,
        )

        location: str = self.form.cleaned_data.get("location")
        nuts318_codes: Union[QuerySet[NutsConversion], List] = (
            get_list_of_nuts318_codes(location) if location else []
        )
        if nuts318_codes:
            filters["nuts3__in"] = nuts318_codes

        sort_by: str = self.form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if not sort_by:
            sort_by = DEFAULT_SORT

        return (
            WebsiteRegister.objects.using("pubsecweb_db")
            .filter(**filters)
            .order_by(sort_by)
        )

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """ Add field values into context """
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        get_without_page: Dict[str, str] = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }

        context["form"] = self.form
        context["url_parameters"] = urllib.parse.urlencode(get_without_page)
        return context


def export_websites(request: HttpRequest) -> HttpResponse:
    """
    View to export websites

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        HttpResponse: Django HttpResponse
    """
    website_search_form: WebsiteSearchForm = WebsiteSearchForm(request.GET)
    website_search_form.is_valid()
    filters: Dict[str, Any] = build_filters(
        cleaned_data=website_search_form.cleaned_data,
        field_and_filter_names=WEBSITE_FIELD_AND_FILTER_NAMES,
    )
    return download_as_csv(
        queryset=WebsiteRegister.objects.using("pubsecweb_db").filter(**filters),
        field_names=WEBSITE_FIELDS_TO_EXPORT,
        filename="websites.csv",
    )
