"""
Views for cases app
"""
from datetime import date, timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Type, Union
import urllib

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from ..audits.forms import (
    AuditStatement1UpdateForm,
    AuditStatement2UpdateForm,
)
from ..audits.utils import get_test_view_tables_context, get_retest_view_tables_context

from ..notifications.utils import add_notification, read_notification

from ..reports.utils import get_report_visits_metrics

from ..comments.forms import CommentCreateForm
from ..comments.models import Comment
from ..comments.utils import add_comment_notification

from ..common.utils import (
    extract_domain_from_url,
    get_id_from_button_name,
    record_model_update_event,
    record_model_create_event,
    check_dict_for_truthy_values,
    list_to_dictionary_of_lists,
)
from ..common.form_extract_utils import (
    extract_form_labels_and_values,
    FieldLabelAndValue,
)
from ..common.utils import amp_format_date
from ..reports.utils import build_issues_tables
from .models import (
    Case,
    Contact,
    REPORT_APPROVED_STATUS_APPROVED,
    TESTING_METHODOLOGY_PLATFORM,
    REPORT_METHODOLOGY_PLATFORM,
)
from .forms import (
    CaseCreateForm,
    CaseDetailUpdateForm,
    CaseContactFormset,
    CaseContactFormsetOneExtra,
    CaseContactsUpdateForm,
    CaseSearchForm,
    CaseTestResultsUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseQAProcessUpdateForm,
    CaseReportCorrespondenceUpdateForm,
    CaseReportFollowupDueDatesUpdateForm,
    CaseNoPSBContactUpdateForm,
    CaseTwelveWeekCorrespondenceUpdateForm,
    CaseTwelveWeekCorrespondenceDueDatesUpdateForm,
    CaseTwelveWeekRetestUpdateForm,
    CaseReviewChangesUpdateForm,
    CaseCloseUpdateForm,
    PostCaseUpdateForm,
    CaseEnforcementBodyCorrespondenceUpdateForm,
    CaseDeactivateForm,
)
from .utils import (
    get_sent_date,
    download_equality_body_cases,
    download_feedback_survey_cases,
    filter_cases,
    replace_search_key_with_case_search,
    download_cases,
    record_case_event,
)

ONE_WEEK_IN_DAYS = 7
FOUR_WEEKS_IN_DAYS = 4 * ONE_WEEK_IN_DAYS
TWELVE_WEEKS_IN_DAYS = 12 * ONE_WEEK_IN_DAYS
TRUTHY_SEARCH_FIELDS: List[str] = [
    "sort_by",
    "status",
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
]
statement_fields = {
    **AuditStatement1UpdateForm().fields,
    **AuditStatement2UpdateForm().fields,
}


def find_duplicate_cases(url: str, organisation_name: str = "") -> QuerySet[Case]:
    """Look for cases with matching domain or organisation name"""
    domain: str = extract_domain_from_url(url)
    if organisation_name:
        return Case.objects.filter(
            Q(organisation_name__icontains=organisation_name) | Q(domain=domain)
        )
    return Case.objects.filter(domain=domain)


def calculate_report_followup_dates(case: Case, report_sent_date: date) -> Case:
    """Calculate followup dates based on a report sent date"""
    if report_sent_date is None:
        case.report_followup_week_1_due_date = None
        case.report_followup_week_4_due_date = None
        case.report_followup_week_12_due_date = None
    else:
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
    case: Case, twelve_week_update_requested_date: date
) -> Case:
    """Calculate chaser dates based on a twelve week update requested date"""
    if twelve_week_update_requested_date is None:
        case.twelve_week_1_week_chaser_due_date = None
    else:
        case.twelve_week_1_week_chaser_due_date = (
            twelve_week_update_requested_date + timedelta(days=ONE_WEEK_IN_DAYS)
        )
    return case


def format_due_date_help_text(due_date: Optional[date]) -> str:
    """Format date and prefix with 'Due' if present"""
    if due_date is None:
        return "None"
    return f"Due {amp_format_date(due_date)}"


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: Type[Case] = Case
    context_object_name: str = "case"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = self.object
        context["contacts"] = self.object.contact_set.filter(is_deleted=False)
        case_details_prefix: List[FieldLabelAndValue] = [
            FieldLabelAndValue(
                label="Date created",
                value=case.created,
                type=FieldLabelAndValue.DATE_TYPE,
            ),
            FieldLabelAndValue(label="Status", value=self.object.get_status_display()),
        ]

        get_case_rows: Callable = partial(
            extract_form_labels_and_values, instance=self.object
        )

        if self.object.report_methodology == REPORT_METHODOLOGY_PLATFORM:
            context.update(get_report_visits_metrics(self.object))

        context["case_details_rows"] = case_details_prefix + get_case_rows(
            form=CaseDetailUpdateForm()
        )
        context["report_details_rows"] = get_case_rows(
            form=CaseReportDetailsUpdateForm()
        )
        context["contact_rows"] = get_case_rows(form=CaseContactsUpdateForm())
        context["review_changes_rows"] = get_case_rows(
            form=CaseReviewChangesUpdateForm()
        )
        context["case_close_rows"] = get_case_rows(form=CaseCloseUpdateForm())
        context["post_case_rows"] = get_case_rows(form=PostCaseUpdateForm())
        context["enforcement_body_correspondence_rows"] = get_case_rows(
            form=CaseEnforcementBodyCorrespondenceUpdateForm()
        )

        if case.audit:
            return {
                **get_test_view_tables_context(audit=case.audit),
                **get_retest_view_tables_context(case=case),
                **context,
            }

        return context


class CaseListView(ListView):
    """
    View of list of cases
    """

    model: Type[Case] = Case
    context_object_name: str = "cases"
    paginate_by: int = 10

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

    def get_queryset(self) -> QuerySet[Case]:
        """Add filters to queryset"""
        if self.form.errors:
            return Case.objects.none()

        return filter_cases(self.form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)

        get_without_page: Dict[str, Union[str, List[object]]] = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }

        context["advanced_search_open"] = check_dict_for_truthy_values(
            dictionary=get_without_page, keys_to_check=TRUTHY_SEARCH_FIELDS
        )
        context["form"] = self.form
        context["url_parameters"] = urllib.parse.urlencode(get_without_page)
        return context


class CaseCreateView(CreateView):
    """
    View to create a case
    """

    model: Type[Case] = Case
    form_class: Type[CaseCreateForm] = CaseCreateForm
    context_object_name: str = "case"
    template_name: str = "cases/forms/create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            case: Case = form.save(commit=False)
            case.created_by = self.request.user
            return super().form_valid(form)

        context: Dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[Case] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)

        case: Case = form.save(commit=False)
        case.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case: Case = self.object
        user: User = self.request.user
        record_model_create_event(user=user, model_object=case)
        record_case_event(user=user, new_case=case)
        case_pk: Dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("cases:edit-case-details", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("cases:case-create")
        elif "save_exit" in self.request.POST:
            url: str = reverse("cases:case-list")
        else:
            url: str = reverse("cases:edit-contact-details", kwargs=case_pk)
        return url


class CaseUpdateView(UpdateView):
    """
    View to update case
    """

    model: Type[Case] = Case
    context_object_name: str = "case"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: Case = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(user=user, model_object=self.object)
            old_case: Case = Case.objects.get(pk=self.object.id)
            record_case_event(user=user, new_case=self.object, old_case=old_case)

            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)

            self.object.save()

            if old_case.status != self.object.status:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    f"Status changed from '{old_case.get_status_display()}'"
                    f" to '{self.object.get_status_display()}'",
                )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class CaseDetailUpdateView(CaseUpdateView):
    """
    View to update case details
    """

    form_class: Type[CaseDetailUpdateForm] = CaseDetailUpdateForm
    template_name: str = "cases/forms/details.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-test-results", kwargs=case_pk)
        return super().get_success_url()


class CaseTestResultsUpdateView(CaseUpdateView):
    """
    View to update case test results
    """

    form_class: Type[CaseTestResultsUpdateForm] = CaseTestResultsUpdateForm
    template_name: str = "cases/forms/test_results.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-report-details", kwargs=case_pk)
        return super().get_success_url()


class CaseReportDetailsUpdateView(CaseUpdateView):
    """
    View to update case report details
    """

    model: Type[Case] = Case
    form_class: Type[CaseReportDetailsUpdateForm] = CaseReportDetailsUpdateForm
    template_name: str = "cases/forms/report_details.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        read_notification(self.request)
        if self.object.report_methodology == REPORT_METHODOLOGY_PLATFORM:
            context.update(get_report_visits_metrics(self.object))
        return context

    def get_form(self):
        """Hide fields if testing using platform"""
        form = super().get_form()
        if self.object.report_methodology == REPORT_METHODOLOGY_PLATFORM:
            for fieldname in [
                "report_draft_url",
                "report_notes",
            ]:
                form.fields[fieldname].widget = forms.HiddenInput()
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-qa-process", kwargs=case_pk)
        return super().get_success_url()


class CaseQAProcessUpdateView(CaseUpdateView):
    """
    View to update QA process
    """

    form_class: Type[CaseQAProcessUpdateForm] = CaseQAProcessUpdateForm
    template_name: str = "cases/forms/qa_process.html"

    def get_form(self):
        """Hide fields if testing using platform"""
        form = super().get_form()
        if self.object.report_methodology == REPORT_METHODOLOGY_PLATFORM:
            for fieldname in [
                "report_final_odt_url",
                "report_final_pdf_url",
            ]:
                form.fields[fieldname].widget = forms.HiddenInput()
        return form

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Notify auditor if case has been QA approved."""
        if form.changed_data and "report_approved_status" in form.changed_data:
            if self.object.report_approved_status == REPORT_APPROVED_STATUS_APPROVED:
                case: Case = self.object
                if case.auditor:
                    add_notification(
                        user=case.auditor,
                        body=f"{self.request.user.get_full_name()} QA approved Case {case}",
                        path=reverse("cases:edit-qa-process", kwargs={"pk": case.id}),
                        list_description=f"{case} - QA process",
                        request=self.request,
                    )
        return super().form_valid(form=form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "add_comment" in self.request.POST:
            return reverse("cases:add-qa-comment", kwargs={"case_id": self.object.id})
        if "save_continue" in self.request.POST:
            return reverse("cases:edit-contact-details", kwargs={"pk": self.object.id})
        return super().get_success_url()


class QACommentCreateView(CreateView):
    """
    View to create a case
    """

    model: Type[Comment] = Comment
    form_class: Type[CommentCreateForm] = CommentCreateForm
    context_object_name: str = "comment"
    template_name: str = "cases/forms/qa_add_comment.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add undeleted contacts to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        self.case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        context["case"] = self.case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        self.case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        comment: Comment = Comment.objects.create(
            case=self.case, user=self.request.user, body=form.cleaned_data.get("body")
        )
        record_model_create_event(user=self.request.user, model_object=comment)
        add_comment_notification(self.request, comment)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case_pk: Dict[str, int] = {"pk": self.case.id}  # type: ignore
        return f"{reverse('cases:edit-qa-process', kwargs=case_pk)}?#qa-discussion"


class CaseContactFormsetUpdateView(CaseUpdateView):
    """
    View to update case contacts
    """

    form_class: Type[CaseContactsUpdateForm] = CaseContactsUpdateForm
    template_name: str = "cases/forms/contact_formset.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            contacts_formset = CaseContactFormset(self.request.POST)
        else:
            contacts: QuerySet[Contact] = self.object.contact_set.filter(
                is_deleted=False
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
                    contact.case = case
                    contact.save()
                    record_model_create_event(
                        user=self.request.user, model_object=contact
                    )
                else:
                    record_model_update_event(
                        user=self.request.user, model_object=contact
                    )
                    contact.save()
        else:
            return super().form_invalid(form)
        contact_id_to_delete: Optional[int] = get_id_from_button_name(
            button_name_prefix="remove_contact_",
            querydict=self.request.POST,
        )
        if contact_id_to_delete is not None:
            contact_to_delete: Contact = Contact.objects.get(id=contact_id_to_delete)
            contact_to_delete.is_deleted = True
            record_model_update_event(
                user=self.request.user, model_object=contact_to_delete
            )
            contact_to_delete.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case_pk: Dict[str, int] = {"pk": self.object.id}
        if "save" in self.request.POST:
            return super().get_success_url()
        elif "save_continue" in self.request.POST:
            return reverse("cases:edit-report-correspondence", kwargs=case_pk)
        elif "add_contact" in self.request.POST:
            return f"{reverse('cases:edit-contact-details', kwargs=case_pk)}?add_extra=true#contact-None"
        else:
            contact_id_to_delete: Optional[int] = get_id_from_button_name(
                "remove_contact_", self.request.POST
            )
            if contact_id_to_delete is not None:
                return reverse("cases:edit-contact-details", kwargs=case_pk)
            else:
                return reverse("cases:case-detail", kwargs=case_pk)


class CaseReportCorrespondenceUpdateView(CaseUpdateView):
    """
    View to update case post report details
    """

    form_class: Type[
        CaseReportCorrespondenceUpdateForm
    ] = CaseReportCorrespondenceUpdateForm
    template_name: str = "cases/forms/report_correspondence.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.object.report_methodology == REPORT_METHODOLOGY_PLATFORM:
            context.update(get_report_visits_metrics(self.object))
        return context

    def get_form(self):
        """Populate help text with dates"""
        form = super().get_form()
        case: Case = form.instance
        form.fields[
            "report_followup_week_1_sent_date"
        ].help_text = format_due_date_help_text(case.report_followup_week_1_due_date)
        form.fields[
            "report_followup_week_4_sent_date"
        ].help_text = format_due_date_help_text(case.report_followup_week_4_due_date)
        return form

    def form_valid(self, form: CaseReportCorrespondenceUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: Case = form.save(commit=False)
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
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-twelve-week-correspondence", kwargs=case_pk)
        return super().get_success_url()


class CaseReportFollowupDueDatesUpdateView(CaseUpdateView):
    """
    View to update report followup due dates
    """

    form_class: Type[
        CaseReportFollowupDueDatesUpdateForm
    ] = CaseReportFollowupDueDatesUpdateForm
    template_name: str = "cases/forms/report_followup_due_dates.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        case_pk: Dict[str, int] = {"pk": self.object.id}
        return reverse("cases:edit-report-correspondence", kwargs=case_pk)


class CaseTwelveWeekCorrespondenceUpdateView(CaseUpdateView):
    """
    View to record week twelve correspondence details
    """

    form_class: Type[
        CaseTwelveWeekCorrespondenceUpdateForm
    ] = CaseTwelveWeekCorrespondenceUpdateForm
    template_name: str = "cases/forms/twelve_week_correspondence.html"

    def get_form(self):
        """Populate help text with dates"""
        form = super().get_form()
        form.fields[
            "twelve_week_1_week_chaser_sent_date"
        ].help_text = format_due_date_help_text(
            form.instance.twelve_week_1_week_chaser_due_date
        )
        return form

    def form_valid(self, form: CaseTwelveWeekCorrespondenceUpdateForm):
        """
        Recalculate chaser dates if twelve week update requested date has changed;
        Otherwise set sent dates based on chaser date checkboxes.
        """
        self.object: Case = form.save(commit=False)
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
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            if case.testing_methodology == TESTING_METHODOLOGY_PLATFORM:
                return reverse("cases:edit-twelve-week-retest", kwargs=case_pk)
            return reverse("cases:edit-review-changes", kwargs=case_pk)
        return super().get_success_url()


class CaseTwelveWeekCorrespondenceDueDatesUpdateView(CaseUpdateView):
    """
    View to update twelve week correspondence followup due dates
    """

    form_class: Type[
        CaseTwelveWeekCorrespondenceDueDatesUpdateForm
    ] = CaseTwelveWeekCorrespondenceDueDatesUpdateForm
    template_name: str = "cases/forms/twelve_week_correspondence_due_dates.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        case_pk: Dict[str, int] = {"pk": self.object.id}
        return reverse("cases:edit-twelve-week-correspondence", kwargs=case_pk)


class CaseTwelveWeekCorrespondenceEmailTemplateView(TemplateView):
    template_name: str = "cases/twelve_week_correspondence_email.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add platform settings to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = get_object_or_404(Case, id=kwargs.get("pk"))
        context["case"] = case
        context["issues_tables"] = build_issues_tables(report=case.report)
        return context


class CaseNoPSBResponseUpdateView(CaseUpdateView):
    """
    View to set no psb contact flag
    """

    form_class: Type[CaseNoPSBContactUpdateForm] = CaseNoPSBContactUpdateForm
    template_name: str = "cases/forms/no_psb_response.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        case_pk: Dict[str, int] = {"pk": self.object.id}
        return reverse("cases:edit-twelve-week-correspondence", kwargs=case_pk)


class CaseTwelveWeekRetestUpdateView(CaseUpdateView):
    """
    View to update case twelve week retest results
    """

    form_class: Type[CaseTwelveWeekRetestUpdateForm] = CaseTwelveWeekRetestUpdateForm
    template_name: str = "cases/forms/twelve_week_retest.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-review-changes", kwargs=case_pk)
        return super().get_success_url()


class CaseReviewChangesUpdateView(CaseUpdateView):
    """
    View to record review of changes made by PSB
    """

    form_class: Type[CaseReviewChangesUpdateForm] = CaseReviewChangesUpdateForm
    template_name: str = "cases/forms/review_changes.html"

    def get_form(self):
        """Populate retested_website_date help text with link to test results for this case"""
        form = super().get_form()
        if form.instance.testing_methodology == TESTING_METHODOLOGY_PLATFORM:
            form.fields["retested_website_date"].help_text = ""
        else:
            if form.instance.test_results_url:
                form.fields["retested_website_date"].help_text = mark_safe(
                    f'The retest form can be found in the <a href="{form.instance.test_results_url}"'
                    ' class="govuk-link govuk-link--no-visited-state" target="_blank">test results</a>'
                )
        return form

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            return reverse("cases:edit-case-close", kwargs=case_pk)
        return super().get_success_url()


class CaseCloseUpdateView(CaseUpdateView):
    """
    View to record sending the compliance decision
    """

    form_class: Type[CaseCloseUpdateForm] = CaseCloseUpdateForm
    template_name: str = "cases/forms/case_close.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-enforcement-body-correspondence", kwargs=case_pk)
        return super().get_success_url()


class CaseEnforcementBodyCorrespondenceUpdateView(CaseUpdateView):
    """
    View to note correspondence with enforcement body
    """

    form_class: Type[
        CaseEnforcementBodyCorrespondenceUpdateForm
    ] = CaseEnforcementBodyCorrespondenceUpdateForm
    template_name: str = "cases/forms/enforcement_body_correspondence.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-post-case", kwargs=case_pk)
        return super().get_success_url()


class PostCaseUpdateView(CaseUpdateView):
    """
    View to record post case notes
    """

    form_class: Type[PostCaseUpdateForm] = PostCaseUpdateForm
    template_name: str = "cases/forms/post_case.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:case-detail", kwargs=case_pk)
        return super().get_success_url()


class CaseDeactivateUpdateView(CaseUpdateView):
    """
    View to deactivate case
    """

    form_class: Type[CaseDeactivateForm] = CaseDeactivateForm
    template_name: str = "cases/forms/deactivate.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = form.save(commit=False)
        case.is_deactivated = True
        case.deactivate_date = date.today()
        record_model_update_event(user=self.request.user, model_object=case)
        case.save()
        return HttpResponseRedirect(case.get_absolute_url())


class CaseReactivateUpdateView(CaseUpdateView):
    """
    View to reactivate case
    """

    form_class: Type[CaseDeactivateForm] = CaseDeactivateForm
    template_name: str = "cases/forms/reactivate.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = form.save(commit=False)
        case.is_deactivated = False
        record_model_update_event(user=self.request.user, model_object=case)
        case.save()
        return HttpResponseRedirect(case.get_absolute_url())


class CaseStatusWorkflowDetailView(DetailView):
    model: Type[Case] = Case
    context_object_name: str = "case"
    template_name: str = "cases/status_workflow.html"


class CaseOutstandingIssuesDetailView(DetailView):
    model: Type[Case] = Case
    context_object_name: str = "case"
    template_name: str = "cases/outstanding_issues.html"

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = self.object

        view_url_param: Union[str, None] = self.request.GET.get("view")
        show_failures_by_page: bool = not view_url_param == "WCAG view"
        context["show_failures_by_page"] = show_failures_by_page

        if case.audit and case.audit.unfixed_check_results:
            if show_failures_by_page:
                context["audit_failures_by_page"] = list_to_dictionary_of_lists(
                    items=case.audit.unfixed_check_results, group_by_attr="page"
                )
            else:
                context["audit_failures_by_wcag"] = list_to_dictionary_of_lists(
                    items=case.audit.unfixed_check_results.order_by(
                        "wcag_definition__name"
                    ),
                    group_by_attr="wcag_definition",
                )

        return context


def export_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases"""
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_cases(cases=filter_cases(form=case_search_form))


def export_equality_body_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases to send to an enforcement body"""
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_equality_body_cases(cases=filter_cases(form=case_search_form))


def export_feedback_suvey_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for feedback survey"""
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_feedback_survey_cases(cases=filter_cases(form=case_search_form))
