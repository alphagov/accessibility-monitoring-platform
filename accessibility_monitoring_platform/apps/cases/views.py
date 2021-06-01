"""
Views for cases
"""
import urllib

from django.views.generic.list import ListView

from .models import Case
from .forms import SearchForm

DEFAULT_SORT = "-id"


class CaseListView(ListView):
    model = Case
    context_object_name = "cases"
    paginate_by = 10

    def get_queryset(self):
        """ Add filters to queryset """
        filters = {}
        form = SearchForm(self.request.GET)
        form.is_valid()
        case_number = form.cleaned_data.get("case_number")
        if case_number:
            filters["id"] = case_number
        domain = form.cleaned_data.get("domain")
        if domain:
            filters["domain__icontains"] = domain
        organisation = form.cleaned_data.get("organisation")
        if organisation:
            filters["website_name__icontains"] = organisation
        auditor = form.cleaned_data.get("auditor")
        if auditor:
            filters["auditor"] = auditor
        status = form.cleaned_data.get("status")
        if status:
            filters["status"] = status
        filters["created__gte"] = form.start_date
        filters["created__lte"] = form.end_date
        sort_by = form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if not sort_by:
            sort_by = DEFAULT_SORT
        return Case.objects.filter(**filters).order_by(sort_by)

    def get_context_data(self, **kwargs):
        """ Add field values into contex """
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        get_without_page: dict = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }
        context["parameters"] = urllib.parse.urlencode(get_without_page)
        context["case_number"] = self.request.GET.get("case-number", "")
        context["auditor"] = self.request.GET.get("auditor", "")
        return context
