"""
Views for cases
"""
import re
import urllib
from typing import Any, Dict, List, Match, Tuple, Union

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Case, Contact
from .forms import (
    CaseCreateForm,
    CaseWebsiteDetailUpdateForm,
    CaseContactFormset,
    CaseContactFormsetOneExtra,
    CaseSearchForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CasePostReportUpdateForm,
)

DEFAULT_SORT: str = "-id"
CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("case_number", "id"),
    ("domain", "domain__icontains"),
    ("organisation", "organisation_name__icontains"),
    ("auditor", "auditor"),
    ("status", "status"),
    ("start_date", "created__gte"),
    ("end_date", "created__lte"),
]


def get_id_from_button_name(button_name_prefix: str, post: Dict) -> Union[int, None]:
    """
    Given a button name in the form: prefix_[id] extract and return the id value.
    """
    encoded_url: str = urllib.parse.urlencode(post)
    match_obj: Union[Match, None] = re.search(
        r"" + button_name_prefix + "\d+", encoded_url
    )
    id: Union[int, None] = None
    if match_obj is not None:
        button_name: str = match_obj.group()
        id: int = int(button_name.replace(button_name_prefix, ""))
    return id


def build_filters(
    cleaned_data: Dict, field_and_filter_names: List[Tuple[str, str]]
) -> Dict:
    """
    Given the form cleaned_data, work through a list of field and filter names
    to build up a dictionary of filters to apply in a queryset.
    """
    filters: Dict = {}
    for field_name, filter_name in field_and_filter_names:
        value: Union[str, None] = cleaned_data.get(field_name)
        if value:
            filters[filter_name] = value
    return filters


class CaseDetailView(DetailView):
    model = Case
    context_object_name = "case"

    def get_context_data(self, **kwargs):
        """ Add unarchived contacts to context """
        context = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contact_set.filter(archived=False)
        return context


class CaseListView(ListView):
    model = Case
    context_object_name = "cases"
    paginate_by = 10

    def get_queryset(self):
        """ Add filters to queryset """
        form: CaseSearchForm = CaseSearchForm(self.request.GET)
        form.is_valid()

        filters: dict = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=CASE_FIELD_AND_FILTER_NAMES,
        )
        filters["archived"] = False

        sort_by: str = form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if not sort_by:
            sort_by = DEFAULT_SORT

        return Case.objects.filter(**filters).order_by(sort_by)

    def get_context_data(self, **kwargs):
        """ Add field values into context """
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        get_without_page: dict = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }

        context["form"] = CaseSearchForm(self.request.GET)
        context["parameters"] = urllib.parse.urlencode(get_without_page)
        context["case_number"] = self.request.GET.get("case-number", "")
        context["auditor"] = self.request.GET.get("auditor", "")
        return context


class CaseCreateView(CreateView):
    model = Case
    form_class = CaseCreateForm
    context_object_name = "case"
    template_name_suffix = "_create_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-contact-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseWebsiteDetailUpdateView(UpdateView):
    model = Case
    form_class = CaseWebsiteDetailUpdateForm
    context_object_name = "case"
    template_name_suffix = "_website_details_update_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-contact-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseContactFormsetUpdateView(UpdateView):
    model = Case
    fields = []
    context_object_name = "case"
    template_name_suffix = "_contact_formset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            contacts_formset = CaseContactFormset(self.request.POST)
        else:
            contacts = self.object.contact_set.filter(archived=False)
            if "add_extra" in self.request.GET:
                contacts_formset = CaseContactFormsetOneExtra(queryset=contacts)
            else:
                contacts_formset = CaseContactFormset(queryset=contacts)
        context["contacts_formset"] = contacts_formset
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context["contacts_formset"]
        case = form.save()
        if contact_formset.is_valid():
            contacts = contact_formset.save(commit=False)
            for contact in contacts:
                if not contact.case_id:
                    contact.case_id = case.id
                contact.save()
        contact_id_to_archive = get_id_from_button_name(
            "remove_contact_", self.request.POST
        )
        if contact_id_to_archive is not None:
            contact_to_archive = Contact.objects.get(id=contact_id_to_archive)
            contact_to_archive.archived = True
            contact_to_archive.save()
        return super().form_valid(form)

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        elif "save_continue" in self.request.POST:
            url = reverse_lazy("cases:edit-test-results", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy("cases:case-list")
        return url


class CaseTestResultsUpdateView(UpdateView):
    model = Case
    form_class = CaseTestResultsUpdateForm
    context_object_name = "case"
    template_name_suffix = "_test_results_update_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-report-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseReportDetailsUpdateView(UpdateView):
    model = Case
    form_class = CaseReportDetailsUpdateForm
    context_object_name = "case"
    template_name_suffix = "_report_details_update_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-post-report-details", kwargs={"pk": self.object.id}
            )
        return url


class CasePostReportDetailsUpdateView(UpdateView):
    model = Case
    form_class = CasePostReportUpdateForm
    context_object_name = "case"
    template_name_suffix = "_post_report_details_update_form"

    def get_success_url(self):
        return reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})


@login_required
def archive_case(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to archive case

    Args:
        request (HttpRequest): Django HttpRequest
        pk: int

    Returns:
        HttpResponse: Django HttpResponse
    """
    case = get_object_or_404(Case, pk=pk)
    case.archived = True
    case.save()
    return redirect(reverse_lazy("cases:case-list"))
