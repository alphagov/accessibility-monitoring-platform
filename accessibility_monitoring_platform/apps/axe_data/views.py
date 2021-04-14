"""
Views of Axe test result data
"""
from datetime import datetime
import urllib

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, Page
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import AxeDataSearchForm, DEFAULT_START_DATE, DEFAULT_END_DATE
from .models import TestresultAxeHeader
from typing import Tuple, Union

PAGE_SIZE = 25


@login_required
def home(request: HttpRequest) -> HttpResponse:
    """
    Search for Axe test result headers

    Args:
        request (HttpRequest): [description]

    Returns:
        HttpResponse: Containing fearch form and results
    """
    context: dict = {}
    parameters: str = ""
    domain_name: str = None
    start_date: datetime = DEFAULT_START_DATE
    end_date: datetime = DEFAULT_END_DATE
    filter_params: dict = {}

    def get_filters_from_form() -> Tuple[str, datetime, datetime]:
        """ Get values to filter TestresultAxeHeader objects from form """
        domain_name: str = form.cleaned_data.get("domain_name")
        start_date: datetime = form.start_date
        end_date: datetime = form.end_date
        return domain_name, start_date, end_date

    if request.POST:
        form: AxeDataSearchForm = AxeDataSearchForm(request.POST)
        if form.is_valid():
            populated_fields: dict = {
                key: value
                for (key, value) in form.cleaned_data.items()
                if value is not None and value != ""
            }
            parameters: str = urllib.parse.urlencode(populated_fields)
            domain_name, start_date, end_date = get_filters_from_form()
    else:
        get_without_page: dict = {
            key: value for (key, value) in request.GET.items() if key != "page"
        }
        form: AxeDataSearchForm = AxeDataSearchForm(get_without_page)
        if form.is_valid():
            parameters: str = urllib.parse.urlencode(get_without_page)
            domain_name, start_date, end_date = get_filters_from_form()

    context["form"]: AxeDataSearchForm = form
    context["parameters"]: str = parameters

    if domain_name or start_date != DEFAULT_START_DATE or end_date != DEFAULT_END_DATE:
        if domain_name is not None:
            filter_params["domain_name__icontains"]: str = domain_name
        filter_params["test_timestamp__gte"]: datetime = start_date
        filter_params["test_timestamp__lte"]: datetime = end_date
        testresult_axe_headers: QuerySet = TestresultAxeHeader.objects.using(
            "a11ymon_db"
        ).filter(**filter_params)
        context["number_of_results"]: int = len(testresult_axe_headers)
        paginator: Paginator = Paginator(testresult_axe_headers, PAGE_SIZE)
        page_number: Union[str, None] = request.GET.get("page")
        context["page_obj"]: Page = paginator.get_page(page_number)

    return render(request, "axe_data/home.html", context)
