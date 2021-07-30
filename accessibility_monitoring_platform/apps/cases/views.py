"""
Views for cases app
"""
from datetime import date, timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Tuple
import urllib

from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.safestring import mark_safe


from ..common.typing import IntOrNone
from ..common.utils import (
    build_filters,
    format_date,
    download_as_csv,
    extract_domain_from_url,
    get_field_names_for_export,
    get_id_from_button_name,
)
from .models import Case, Contact
from .forms import (
    CaseCreateForm,
    CaseDetailUpdateForm,
    CaseContactFormset,
    CaseContactFormsetOneExtra,
    CaseContactsUpdateForm,
    CaseSearchForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportCorrespondenceUpdateForm,
    CaseReportFollowupDueDatesUpdateForm,
    CaseArchiveForm,
    CaseNoPSBContactUpdateForm,
    CaseTwelveWeekCorrespondenceUpdateForm,
    CaseTwelveWeekCorrespondenceDueDatesUpdateForm,
    CaseFinalDecisionUpdateForm,
    CaseEnforcementBodyCorrespondenceUpdateForm,
    DEFAULT_SORT,
)
from .utils import CaseFieldLabelAndValue, extract_labels_and_values, get_sent_date

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("start_date", "created__gte"),
    ("end_date", "created__lte"),
]
ONE_WEEK_IN_DAYS = 7
FOUR_WEEKS_IN_DAYS = 4 * ONE_WEEK_IN_DAYS
TWELVE_WEEKS_IN_DAYS = 12 * ONE_WEEK_IN_DAYS


def find_duplicate_cases(url: str, organisation_name: str = "") -> QuerySet[Case]:
    """Look for cases with matching domain or organisation name"""
    domain: str = extract_domain_from_url(url)
    if organisation_name:
        return Case.objects.filter(
            Q(organisation_name__icontains=organisation_name) | Q(domain=domain)
        )
    return Case.objects.filter(domain=domain)


def calculate_report_followup_dates(
    case: CaseReportCorrespondenceUpdateForm, report_sent_date: date
) -> CaseReportCorrespondenceUpdateForm:
    """Calculate followup dates based on a report sent date"""
    case.report_followup_week_1_due_date = report_sent_date + timedelta(
        days=ONE_WEEK_IN_DAYS
    )
    case.report_followup_week_4_due_date = report_sent_date + timedelta(
        days=FOUR_WEEKS_IN_DAYS
    )
    case.report_followup_week_12_due_date = report_sent_date + timedelta(
        days=TWELVE_WEEKS_IN_DAYS
    )
    return case


def calculate_twelve_week_chaser_dates(
    case: CaseTwelveWeekCorrespondenceUpdateForm,
    twelve_week_update_requested_date: date,
) -> CaseTwelveWeekCorrespondenceUpdateForm:
    """Calculate chaser dates based on a twelve week update requested date"""
    case.twelve_week_1_week_chaser_due_date = (
        twelve_week_update_requested_date + timedelta(days=ONE_WEEK_IN_DAYS)
    )
    case.twelve_week_4_week_chaser_due_date = (
        twelve_week_update_requested_date + timedelta(days=FOUR_WEEKS_IN_DAYS)
    )
    return case


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: Case = Case
    context_object_name: str = "case"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add unarchived contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contact_set.filter(is_archived=False)
        case_details_prefix: List[CaseFieldLabelAndValue] = [
            CaseFieldLabelAndValue(
                label="Date created",
                value=self.object.created,
                type=CaseFieldLabelAndValue.DATE_TYPE,
            ),
            CaseFieldLabelAndValue(
                label="Status", value=self.object.get_status_display()
            ),
        ]
        get_rows: Callable = partial(extract_labels_and_values, case=self.object)

        context["case_details_rows"] = case_details_prefix + get_rows(form=CaseDetailUpdateForm())
        context["testing_details_rows"] = get_rows(form=CaseTestResultsUpdateForm())
        context["report_details_rows"] = get_rows(form=CaseReportDetailsUpdateForm())
        context["final_decision_rows"] = get_rows(form=CaseFinalDecisionUpdateForm())
        context["enforcement_body_correspondence_rows"] = get_rows(form=CaseEnforcementBodyCorrespondenceUpdateForm())
        return context


class CaseListView(ListView):
    """
    View of list of cases
    """

    model: Case = Case
    context_object_name: str = "cases"
    paginate_by: int = 10

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.form: CaseSearchForm = CaseSearchForm(self.request.GET)
            self.form.is_valid()
        else:
            self.form = CaseSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Case]:
        """Add filters to queryset"""
        if self.form.errors:
            return Case.objects.none()

        filters: Dict = {}
        search_query = Q()
        sort_by: str = DEFAULT_SORT

        if hasattr(self.form, "cleaned_data"):
            filters: Dict[str, Any] = build_filters(
                cleaned_data=self.form.cleaned_data,
                field_and_filter_names=CASE_FIELD_AND_FILTER_NAMES,
            )
            sort_by: str = self.form.cleaned_data.get("sort_by", DEFAULT_SORT)
            if not sort_by:
                sort_by: str = DEFAULT_SORT
            if self.form.cleaned_data["search"]:
                search_query = (
                    Q(organisation_name__icontains=self.form.cleaned_data["search"])
                    | Q(home_page_url__icontains=self.form.cleaned_data["search"])
                    | Q(id__icontains=self.form.cleaned_data["search"])
                )

        filters["is_archived"] = False

        if "auditor_id" in filters and filters["auditor_id"] == "none":
            filters["auditor_id"] = None
        if "reviewer_id" in filters and filters["reviewer_id"] == "none":
            filters["reviewer_id"] = None

        return Case.objects.filter(search_query, **filters).order_by(sort_by)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
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
    template_name: str = "cases/forms/create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            return super().form_valid(form)

        context: Dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[Case] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        )

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue_case" in self.request.POST:
            url = reverse_lazy("cases:edit-case-details", kwargs={"pk": self.object.id})
        elif "save_new_case" in self.request.POST:
            url = reverse_lazy("cases:case-create")
        elif "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-list")
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
    template_name: str = "cases/forms/details.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
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
    form_class: CaseContactsUpdateForm = CaseContactsUpdateForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/contact_formset.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
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
        """Process contents of valid form"""
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
        """Detect the submit button used and act accordingly"""
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
    template_name: str = "cases/forms/test_results.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
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
    template_name: str = "cases/forms/report_details.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-report-correspondence", kwargs={"pk": self.object.id}
            )
        return url


class CaseReportCorrespondenceUpdateView(UpdateView):
    """
    View to update case post report details
    """

    model: Case = Case
    form_class: CaseReportCorrespondenceUpdateForm = CaseReportCorrespondenceUpdateForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/report_correspondence.html"

    def get_form(self):
        """Populate help text with dates"""
        form = super().get_form()
        form.fields["report_followup_week_1_sent_date"].help_text = format_date(
            form.instance.report_followup_week_1_due_date
        )
        form.fields["report_followup_week_4_sent_date"].help_text = format_date(
            form.instance.report_followup_week_4_due_date
        )
        form.fields["report_followup_week_12_due_date"].help_text = format_date(
            form.instance.report_followup_week_12_due_date
        )
        return form

    def form_valid(self, form: CaseReportCorrespondenceUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: CaseReportCorrespondenceUpdateForm = form.save(commit=False)
        case_from_db: Case = Case.objects.get(pk=self.object.id)
        if "report_sent_date" in form.changed_data:
            self.object = calculate_report_followup_dates(
                case=self.object, report_sent_date=form.cleaned_data["report_sent_date"]
            )
        else:
            for sent_date_name in [
                "report_followup_week_1_sent_date",
                "report_followup_week_4_sent_date",
            ]:
                setattr(
                    self.object,
                    sent_date_name,
                    get_sent_date(form, case_from_db, sent_date_name),
                )
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        if "save_exit" in self.request.POST:
            return reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            return reverse_lazy(
                "cases:edit-12-week-correspondence", kwargs={"pk": self.object.id}
            )


class CaseReportFollowupDueDatesUpdateView(UpdateView):
    """
    View to update report followup due dates
    """

    model: Case = Case
    form_class: CaseReportFollowupDueDatesUpdateForm = (
        CaseReportFollowupDueDatesUpdateForm
    )
    context_object_name: str = "case"
    template_name: str = "cases/forms/report_followup_due_dates.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        return reverse_lazy(
            "cases:edit-report-correspondence", kwargs={"pk": self.object.id}
        )


class CaseTwelveWeekCorrespondenceUpdateView(UpdateView):
    """
    View to record week twelve correspondence details
    """

    model: Case = Case
    form_class: CaseTwelveWeekCorrespondenceUpdateForm = (
        CaseTwelveWeekCorrespondenceUpdateForm
    )
    context_object_name: str = "case"
    template_name: str = "cases/forms/twelve_week_correspondence.html"

    def get_form(self):
        """Populate help text with dates"""
        form = super().get_form()
        form.fields["report_followup_week_12_due_date"].help_text = format_date(
            form.instance.report_followup_week_12_due_date
        )
        form.fields["twelve_week_1_week_chaser_sent_date"].help_text = format_date(
            form.instance.twelve_week_1_week_chaser_due_date
        )
        form.fields["twelve_week_4_week_chaser_sent_date"].help_text = format_date(
            form.instance.twelve_week_4_week_chaser_due_date
        )
        return form

    def form_valid(self, form: CaseTwelveWeekCorrespondenceUpdateForm):
        """
        Recalculate chaser dates if twelve week update requested date has changed;
        Otherwise set sent dates based on chaser date checkboxes.
        """
        self.object: CaseTwelveWeekCorrespondenceUpdateForm = form.save(commit=False)
        case_from_db: Case = Case.objects.get(pk=self.object.id)
        if "twelve_week_update_requested_date" in form.changed_data:
            self.object = calculate_twelve_week_chaser_dates(
                case=self.object,
                twelve_week_update_requested_date=form.cleaned_data[
                    "twelve_week_update_requested_date"
                ],
            )
        else:
            for sent_date_name in [
                "twelve_week_1_week_chaser_sent_date",
                "twelve_week_4_week_chaser_sent_date",
            ]:
                setattr(
                    self.object,
                    sent_date_name,
                    get_sent_date(form, case_from_db, sent_date_name),
                )
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-final-decision",
                kwargs={"pk": self.object.id},
            )
        return url


class CaseTwelveWeekCorrespondenceDueDatesUpdateView(UpdateView):
    """
    View to update twelve week correspondence followup due dates
    """

    model: Case = Case
    form_class: CaseTwelveWeekCorrespondenceDueDatesUpdateForm = (
        CaseTwelveWeekCorrespondenceDueDatesUpdateForm
    )
    context_object_name: str = "case"
    template_name: str = "cases/forms/twelve_week_correspondence_due_dates.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        return reverse_lazy(
            "cases:edit-12-week-correspondence", kwargs={"pk": self.object.id}
        )


class CaseNoPSBResponseUpdateView(UpdateView):
    """
    View to set no psb contact flag
    """

    model: Case = Case
    form_class: CaseNoPSBContactUpdateForm = CaseNoPSBContactUpdateForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/no_psb_response.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-enforcement-body-correspondence",
                kwargs={"pk": self.object.id},
            )
        return url


class CaseFinalDecisionUpdateView(UpdateView):
    """
    View to record final decision details
    """

    model: Case = Case
    form_class: CaseFinalDecisionUpdateForm = CaseFinalDecisionUpdateForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/final_decision.html"

    def get_form(self):
        """Populate retested_website help text with link to test results for this case"""
        form = super().get_form()
        if form.instance.test_results_url:
            form.fields["retested_website"].help_text = mark_safe(
                f'The retest form can be found in the <a href="{form.instance.test_results_url}"'
                ' class="govuk-link govuk-link--no-visited-state">test results</a>'
            )
        return form

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-enforcement-body-correspondence",
                kwargs={"pk": self.object.id},
            )
        return url


class CaseEnforcementBodyCorrespondenceUpdateView(UpdateView):
    """
    View to note correspondence with enforcement body
    """

    model: Case = Case
    form_class: CaseEnforcementBodyCorrespondenceUpdateForm = (
        CaseEnforcementBodyCorrespondenceUpdateForm
    )
    context_object_name: str = "case"
    template_name: str = "cases/forms/enforcement_body_correspondence.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        return reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})


class CaseArchiveUpdateView(UpdateView):
    """
    View to archive case
    """

    model: Case = Case
    form_class: CaseArchiveForm = CaseArchiveForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/archive.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = form.save(commit=False)
        case.is_archived = True
        case.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        return reverse_lazy("cases:case-list")


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
        field_names=get_field_names_for_export(Case),
        filename="cases.csv",
        include_contact=True,
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
        field_names=get_field_names_for_export(Case),
        filename=f"case_#{pk}.csv",
        include_contact=True,
    )
