"""
Views for cases app
"""
import urllib
from typing import Any, Dict, List, Tuple
from django.db.models.query import QuerySet
from django.forms.models import ModelForm

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from ..common.typing import IntOrNone
from ..common.utils import build_filters, download_as_csv, get_id_from_button_name
from .models import Case, Contact
from .forms import (
    CaseCreateForm,
    CaseDetailUpdateForm,
    CaseContactFormset,
    CaseContactFormsetOneExtra,
    CaseSearchForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CasePostReportUpdateForm,
    DEFAULT_SORT,
)

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("case_number", "id"),
    ("domain", "domain__icontains"),
    ("organisation", "organisation_name__icontains"),
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("start_date", "created__gte"),
    ("end_date", "created__lte"),
]
CASE_FIELDS_TO_EXPORT: List[str] = [
    "status",
    "created",
    "auditor",
    "test_type",
    "home_page_url",
    "domain",
    "application",
    "organisation_name",
    "website_type",
    "sector",
    "region",
    "case_origin",
    "zendesk_url",
    "trello_url",
    "notes",
    "is_public_sector_body",
    "test_results_url",
    "test_status",
    "is_website_compliant",
    "test_notes",
    "report_draft_url",
    "report_review_status",
    "reviewer",
    "report_approved_status",
    "reviewer_notes",
    "report_final_url",
    "report_sent_date",
    "report_acknowledged_date",
    "week_12_followup_date",
    "psb_progress_notes",
    "week_12_followup_email_sent_date",
    "week_12_followup_email_acknowledgement_date",
    "is_website_retested",
    "is_disproportionate_claimed",
    "disproportionate_notes",
    "accessibility_statement_decison",
    "accessibility_statement_url",
    "accessibility_statement_notes",
    "compliance_decision",
    "compliance_decision_notes",
    "compliance_email_sent_date",
    "sent_to_enforcement_body_sent_date",
    "is_case_completed",
    "completed",
    "is_archived",
]


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: Case = Case
    context_object_name: str = "case"
    template_name_suffix: str = "_detail"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """ Add unarchived contacts to context """
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contact_set.filter(is_archived=False)
        return context


class CaseListView(ListView):
    """
    View of list of cases
    """

    model: Case = Case
    context_object_name: str = "cases"
    paginate_by: int = 10

    def get(self, request, *args, **kwargs):
        """ Populate filter form """
        if self.request.GET:
            self.form: CaseSearchForm = CaseSearchForm(self.request.GET)
            self.form.is_valid()
        else:
            self.form = CaseSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Case]:
        """ Add filters to queryset """
        if self.form.errors:
            return Case.objects.none()

        filters: Dict = {}
        sort_by: str = DEFAULT_SORT

        if hasattr(self.form, "cleaned_data"):
            filters: Dict[str, Any] = build_filters(
                cleaned_data=self.form.cleaned_data,
                field_and_filter_names=CASE_FIELD_AND_FILTER_NAMES,
            )
            sort_by: str = self.form.cleaned_data.get("sort_by", DEFAULT_SORT)
            if not sort_by:
                sort_by: str = DEFAULT_SORT

        filters["is_archived"] = False

        if "auditor_id" in filters and filters["auditor_id"] == "none":
            filters["auditor_id"] = None
        if "reviewer_id" in filters and filters["reviewer_id"] == "none":
            filters["reviewer_id"] = None

        return Case.objects.filter(**filters).order_by(sort_by)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """ Add field values into context """
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        get_without_page: Dict[str, str] = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }

        context["form"] = self.form
        context["url_parameters"] = urllib.parse.urlencode(get_without_page)
        return context


class CaseCreateView(CreateView):
    """
    View to create a case
    """

    model: Case = Case
    form_class: CaseCreateForm = CaseCreateForm
    context_object_name: str = "case"
    template_name_suffix: str = "_create_form"

    def get_success_url(self) -> str:
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-contact-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseDetailUpdateView(UpdateView):
    """
    View to update case details
    """

    model: Case = Case
    form_class: CaseDetailUpdateForm = CaseDetailUpdateForm
    context_object_name: str = "case"
    template_name_suffix: str = "_details_update_form"

    def get_success_url(self) -> str:
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-contact-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseContactFormsetUpdateView(UpdateView):
    """
    View to update case contacts
    """

    model: Case = Case
    fields: List[str] = []
    context_object_name: str = "case"
    template_name_suffix: str = "_contact_formset"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """ Get context data for template rendering """
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            contacts_formset = CaseContactFormset(self.request.POST)
        else:
            contacts: QuerySet[Contact] = self.object.contact_set.filter(
                is_archived=False
            )
            if "add_extra" in self.request.GET:
                contacts_formset = CaseContactFormsetOneExtra(queryset=contacts)
            else:
                contacts_formset = CaseContactFormset(queryset=contacts)
        context["contacts_formset"] = contacts_formset
        return context

    def form_valid(self, form: ModelForm):
        """ Process contents of valid form """
        context: Dict[str, Any] = self.get_context_data()
        contact_formset = context["contacts_formset"]
        case: Case = form.save()
        if contact_formset.is_valid():
            contacts: List[Contact] = contact_formset.save(commit=False)
            for contact in contacts:
                if not contact.case_id:
                    contact.case_id = case.id
                contact.save()
        contact_id_to_archive: IntOrNone = get_id_from_button_name(
            button_name_prefix="remove_contact_",
            querydict=self.request.POST,
        )
        if contact_id_to_archive is not None:
            contact_to_archive: Contact = Contact.objects.get(id=contact_id_to_archive)
            contact_to_archive.is_archived = True
            contact_to_archive.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        elif "save_continue" in self.request.POST:
            url = reverse_lazy("cases:edit-test-results", kwargs={"pk": self.object.id})
        elif "add_contact" in self.request.POST:
            url = f"{reverse_lazy('cases:edit-contact-details', kwargs={'pk': self.object.id})}?add_extra=true"
        else:
            contact_id_to_archive: IntOrNone = get_id_from_button_name(
                "remove_contact_", self.request.POST
            )
            if contact_id_to_archive is not None:
                url = reverse_lazy(
                    "cases:edit-contact-details", kwargs={"pk": self.object.id}
                )
            else:
                url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        return url


class CaseTestResultsUpdateView(UpdateView):
    """
    View to update case test results
    """

    model: Case = Case
    form_class: CaseTestResultsUpdateForm = CaseTestResultsUpdateForm
    context_object_name: str = "case"
    template_name_suffix: str = "_test_results_update_form"

    def get_success_url(self) -> str:
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-report-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseReportDetailsUpdateView(UpdateView):
    """
    View to update case report details
    """

    model: Case = Case
    form_class: CaseReportDetailsUpdateForm = CaseReportDetailsUpdateForm
    context_object_name: str = "case"
    template_name_suffix: str = "_report_details_update_form"

    def get_success_url(self) -> str:
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-post-report-details", kwargs={"pk": self.object.id}
            )
        return url


class CasePostReportDetailsUpdateView(UpdateView):
    """
    View to update case post report details
    """

    model: Case = Case
    form_class: CasePostReportUpdateForm = CasePostReportUpdateForm
    context_object_name: str = "case"
    template_name_suffix: str = "_post_report_details_update_form"

    def get_success_url(self) -> str:
        """ Work out url to redirect to on success """
        return reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})


def export_cases(request: HttpRequest) -> HttpResponse:
    """
    View to export cases

    Args:
        request (HttpRequest): Django HttpRequest

    Returns:
        HttpResponse: Django HttpResponse
    """
    case_search_form: CaseSearchForm = CaseSearchForm(request.GET)
    case_search_form.is_valid()
    filters: Dict[str, Any] = build_filters(
        cleaned_data=case_search_form.cleaned_data,
        field_and_filter_names=CASE_FIELD_AND_FILTER_NAMES,
    )
    return download_as_csv(
        queryset=Case.objects.filter(**filters),
        field_names=CASE_FIELDS_TO_EXPORT,
        filename="cases.csv",
    )


def export_single_case(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to export a single case in csv format

    Args:
        request (HttpRequest): Django HttpRequest
        pk: int

    Returns:
        HttpResponse: Django HttpResponse
    """
    return download_as_csv(
        queryset=Case.objects.filter(id=pk),
        field_names=CASE_FIELDS_TO_EXPORT,
        filename=f"case_#{pk}.csv",
    )


def archive_case(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to archive case

    Args:
        request (HttpRequest): Django HttpRequest
        pk: int

    Returns:
        HttpResponse: Django HttpResponse
    """
    case: Case = get_object_or_404(Case, pk=pk)
    case.is_archived = True
    case.save()
    return redirect(reverse_lazy("cases:case-list"))
