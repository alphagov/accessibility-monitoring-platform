"""
Views for cases
"""
from django.views.generic.list import ListView

from .models import Case


class CaseListView(ListView):
    model = Case
    paginate_by = 10

    def get_queryset(self):
        """ Add filters to queryset """
        filters = {}
        case_number = self.request.GET.get("case-number")
        if case_number:
            filters["id"] = case_number
        auditor = self.request.GET.get("auditor")
        if auditor:
            filters["auditor"] = auditor
        return Case.objects.filter(**filters)

    def get_context_data(self, **kwargs):
        """ Add field values into contex """
        context = super().get_context_data(**kwargs)
        context["case_number"] = self.request.GET.get("case-number", "")
        context["auditor"] = self.request.GET.get("auditor", "")
        return context