"""
Views for cases app
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..audits.forms import (
    ArchiveAuditStatement1UpdateForm,
    ArchiveAuditStatement2UpdateForm,
)
from ..audits.utils import report_data_updated
from ..comments.models import Comment
from ..comments.utils import add_comment_notification
from ..common.models import Boolean, EmailTemplate
from ..common.sitemap import Sitemap
from ..common.utils import (
    amp_format_date,
    check_dict_for_truthy_values,
    extract_domain_from_url,
    get_dict_without_page_items,
    get_id_from_button_name,
    get_url_parameters_for_pagination,
    list_to_dictionary_of_lists,
    record_model_create_event,
    record_model_update_event,
)
from ..exports.csv_export_utils import (
    EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
    EqualityBodyCSVColumn,
    download_cases,
    download_feedback_survey_cases,
    populate_equality_body_columns,
)
from ..notifications.models import Task
from ..notifications.utils import add_task
from ..reports.utils import (
    build_issues_tables,
    get_report_visits_metrics,
    publish_report_util,
)
from .forms import (
    CaseCloseUpdateForm,
    CaseCreateForm,
    CaseDeactivateForm,
    CaseEnforcementRecommendationUpdateForm,
    CaseEqualityBodyMetadataUpdateForm,
    CaseFourWeekContactDetailsUpdateForm,
    CaseMetadataUpdateForm,
    CaseNoPSBContactUpdateForm,
    CaseOneWeekContactDetailsUpdateForm,
    CaseOneWeekFollowupFinalUpdateForm,
    CasePublishReportUpdateForm,
    CaseQACommentsUpdateForm,
    CaseReportAcknowledgedUpdateForm,
    CaseReportApprovedUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportFourWeekFollowupUpdateForm,
    CaseReportOneWeekFollowupUpdateForm,
    CaseReportSentOnUpdateForm,
    CaseRequestContactDetailsUpdateForm,
    CaseReviewChangesUpdateForm,
    CaseSearchForm,
    CaseStatementEnforcementUpdateForm,
    CaseTestResultsUpdateForm,
    CaseTwelveWeekRetestUpdateForm,
    CaseTwelveWeekUpdateAcknowledgedUpdateForm,
    CaseTwelveWeekUpdateRequestedUpdateForm,
    ContactCreateForm,
    ContactUpdateForm,
    EqualityBodyCorrespondenceCreateForm,
    ListCaseEqualityBodyCorrespondenceUpdateForm,
    ManageContactDetailsUpdateForm,
    PostCaseUpdateForm,
    ZendeskTicketCreateUpdateForm,
)
from .models import (
    ONE_WEEK_IN_DAYS,
    Case,
    Contact,
    EqualityBodyCorrespondence,
    ZendeskTicket,
)
from .utils import (
    filter_cases,
    get_case_detail_sections,
    record_case_event,
    replace_search_key_with_case_search,
)

FOUR_WEEKS_IN_DAYS: int = 4 * ONE_WEEK_IN_DAYS
TWELVE_WEEKS_IN_DAYS: int = 12 * ONE_WEEK_IN_DAYS
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
    "subcategory",
]
REMOVE_CONTACT_BUTTON_PREFIX: str = "remove_contact_"
statement_fields = {
    **ArchiveAuditStatement1UpdateForm().fields,
    **ArchiveAuditStatement2UpdateForm().fields,
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


def calculate_no_contact_chaser_dates(
    case: Case, seven_day_no_contact_email_sent_date: date
) -> Case:
    """Calculate chaser dates based on seven day no contact sent date"""
    if seven_day_no_contact_email_sent_date is None:
        case.no_contact_one_week_chaser_due_date = None
        case.no_contact_four_week_chaser_due_date = None
    else:
        case.no_contact_one_week_chaser_due_date = (
            seven_day_no_contact_email_sent_date + timedelta(days=ONE_WEEK_IN_DAYS)
        )
        case.no_contact_four_week_chaser_due_date = (
            seven_day_no_contact_email_sent_date + timedelta(days=FOUR_WEEKS_IN_DAYS)
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
        sitemap: Sitemap = Sitemap(request=self.request)

        if not case.report:
            context.update(get_report_visits_metrics(case))

        return {
            **{
                "case_detail_sections": get_case_detail_sections(
                    case=case, sitemap=sitemap
                )
            },
            **context,
        }


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

        context["advanced_search_open"] = check_dict_for_truthy_values(
            dictionary=get_dict_without_page_items(self.request.GET.items()),
            keys_to_check=TRUTHY_SEARCH_FIELDS,
        )
        context["form"] = self.form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
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
            url: str = reverse("cases:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("cases:case-create")
        elif "save_exit" in self.request.POST:
            url: str = reverse("cases:case-list")
        else:
            url: str = reverse("cases:manage-contact-details", kwargs=case_pk)
        return url


class CaseUpdateView(UpdateView):
    """
    View to update case
    """

    model: Type[Case] = Case
    context_object_name: str = "case"
    template_name: str = "common/case_form.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: Case = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(user=user, model_object=self.object)
            old_case: Case = Case.objects.get(pk=self.object.id)
            old_status: str = old_case.status
            record_case_event(user=user, new_case=self.object, old_case=old_case)

            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)

            self.object.save()

            if old_status.status != self.object.status.status:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    f"Status changed from '{old_status.get_status_display()}'"
                    f" to '{self.object.status.get_status_display()}'",
                )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        return self.request.path


class CaseMetadataUpdateView(CaseUpdateView):
    """
    View to update case metadata
    """

    form_class: Type[CaseMetadataUpdateForm] = CaseMetadataUpdateForm

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = self.object
        if case.published_report_url:
            if (
                "enforcement_body" in form.changed_data
                or "home_page_url" in form.changed_data
                or "organisation_name" in form.changed_data
            ):
                report_data_updated(audit=case.audit)
        return super().form_valid(form=form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            if case.audit:
                return reverse(
                    "audits:edit-audit-metadata", kwargs={"pk": case.audit.id}
                )
            return reverse("cases:edit-test-results", kwargs={"pk": case.id})
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
        case: Case = self.object
        if case.report:
            context.update(get_report_visits_metrics(case=case))
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-qa-comments", kwargs=case_pk)
        return super().get_success_url()


class CaseQACommentsUpdateView(CaseUpdateView):
    """
    View to update QA comments page
    """

    form_class: Type[CaseQACommentsUpdateForm] = CaseQACommentsUpdateForm
    template_name: str = "cases/forms/qa_comments.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = self.object
        body: str = form.cleaned_data.get("body")
        if body:
            comment: Comment = Comment.objects.create(
                case=case, user=self.request.user, body=form.cleaned_data.get("body")
            )
            record_model_create_event(user=self.request.user, model_object=comment)
            add_comment_notification(self.request, comment)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse("cases:edit-report-approved", kwargs={"pk": self.object.id})
        return super().get_success_url()


class CaseReportApprovedUpdateView(CaseUpdateView):
    """
    View to update QA auditor
    """

    form_class: Type[CaseReportApprovedUpdateForm] = CaseReportApprovedUpdateForm
    template_name: str = "cases/forms/report_approved.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Notify auditor if case has been QA approved."""
        if form.changed_data and "report_approved_status" in form.changed_data:
            if self.object.report_approved_status == Case.ReportApprovedStatus.APPROVED:
                case: Case = self.object
                if case.auditor:
                    add_task(
                        user=case.auditor,
                        case=case,
                        type=Task.Type.REPORT_APPROVED,
                        description=f"{self.request.user.get_full_name()} QA approved Case {case}",
                        list_description=f"{case} - Report approved",
                        request=self.request,
                    )
        return super().form_valid(form=form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse("cases:edit-publish-report", kwargs={"pk": self.object.id})
        return super().get_success_url()


class CasePublishReportUpdateView(CaseUpdateView):
    """
    View to publish report after QA approval
    """

    form_class: Type[CasePublishReportUpdateForm] = CasePublishReportUpdateForm
    template_name: str = "cases/forms/publish_report.html"

    def form_valid(self, form: ModelForm):
        """Publish report if requested"""
        case: Case = self.object
        if "create_html_report" in self.request.POST:
            publish_report_util(report=case.report, request=self.request)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:manage-contact-details", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class ManageContactDetailsUpdateView(CaseUpdateView):
    """
    View to list case contacts
    """

    form_class: Type[ManageContactDetailsUpdateForm] = ManageContactDetailsUpdateForm
    template_name: str = "cases/forms/manage_contact_details.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            if case.enable_correspondence_process is True:
                return reverse("cases:edit-request-contact-details", kwargs=case_pk)
            else:
                return reverse("cases:edit-report-sent-on", kwargs=case_pk)
        return super().get_success_url()


class ContactCreateView(CreateView):
    """
    View to create case contact
    """

    model: Type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: Type[ContactCreateForm] = ContactCreateForm
    template_name: str = "cases/forms/contact_create.html"

    def form_valid(self, form: ContactCreateForm):
        """Populate case of contact"""
        case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        contact: Contact = form.save(commit=False)
        contact.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        case_pk: Dict[str, int] = {"pk": case.id}
        return reverse("cases:manage-contact-details", kwargs=case_pk)


class ContactUpdateView(UpdateView):
    """
    View to create case contact
    """

    model: Type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: Type[ContactUpdateForm] = ContactUpdateForm
    template_name: str = "cases/forms/contact_update.html"

    def form_valid(self, form: ContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        contact: Contact = form.save(commit=False)
        if "delete_contact" in self.request.POST:
            contact.is_deleted = True
        record_model_update_event(user=self.request.user, model_object=contact)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        case_pk: Dict[str, int] = {"pk": self.object.case.id}
        return reverse("cases:manage-contact-details", kwargs=case_pk)


class CaseRequestContactDetailsUpdateView(CaseUpdateView):
    """
    View to update Request contact details
    """

    form_class: Type[CaseRequestContactDetailsUpdateForm] = (
        CaseRequestContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/request_initial_contact.html"

    def form_valid(self, form: CaseReportSentOnUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: Case = form.save(commit=False)
        if "seven_day_no_contact_email_sent_date" in form.changed_data:
            self.object = calculate_no_contact_chaser_dates(
                case=self.object,
                seven_day_no_contact_email_sent_date=form.cleaned_data[
                    "seven_day_no_contact_email_sent_date"
                ],
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-one-week-contact-details", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseOneWeekContactDetailsUpdateView(CaseUpdateView):
    """
    View to update One week contact details
    """

    form_class: Type[CaseOneWeekContactDetailsUpdateForm] = (
        CaseOneWeekContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/one_week_followup_contact.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-four-week-contact-details", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseFourWeekContactDetailsUpdateView(CaseUpdateView):
    """
    View to update Four week contact details
    """

    form_class: Type[CaseFourWeekContactDetailsUpdateForm] = (
        CaseFourWeekContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/four_week_followup_contact.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse("cases:edit-no-psb-response", kwargs={"pk": self.object.id})
        return super().get_success_url()


class CaseNoPSBResponseUpdateView(CaseUpdateView):
    """
    View to set no psb contact flag
    """

    form_class: Type[CaseNoPSBContactUpdateForm] = CaseNoPSBContactUpdateForm
    template_name: str = "cases/forms/no_psb_response.html"

    def get_success_url(self) -> str:
        """Work out url to redirect to on success"""
        case: Case = self.object
        case_pk: Dict[str, int] = {"pk": case.id}
        if "save_continue" in self.request.POST:
            if case.no_psb_contact == Boolean.YES:
                return reverse("cases:edit-enforcement-recommendation", kwargs=case_pk)
            return reverse("cases:edit-report-sent-on", kwargs=case_pk)
        return super().get_success_url()


class CaseReportSentOnUpdateView(CaseUpdateView):
    """
    View to update Report sent on
    """

    form_class: Type[CaseReportSentOnUpdateForm] = CaseReportSentOnUpdateForm
    template_name: str = "cases/forms/report_sent_on.html"

    def form_valid(self, form: CaseReportSentOnUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: Case = form.save(commit=False)
        if "report_sent_date" in form.changed_data:
            self.object = calculate_report_followup_dates(
                case=self.object, report_sent_date=form.cleaned_data["report_sent_date"]
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-report-one-week-followup", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseReportOneWeekFollowupUpdateView(CaseUpdateView):
    """
    View to update One week followup
    """

    form_class: Type[CaseReportOneWeekFollowupUpdateForm] = (
        CaseReportOneWeekFollowupUpdateForm
    )
    template_name: str = "cases/forms/report_one_week_followup.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-report-four-week-followup", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseReportFourWeekFollowupUpdateView(CaseUpdateView):
    """
    View to update Four week followup
    """

    form_class: Type[CaseReportFourWeekFollowupUpdateForm] = (
        CaseReportFourWeekFollowupUpdateForm
    )
    template_name: str = "cases/forms/report_four_week_followup.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-report-acknowledged", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseReportAcknowledgedUpdateView(CaseUpdateView):
    """
    View to update Report acknowledged
    """

    form_class: Type[CaseReportAcknowledgedUpdateForm] = (
        CaseReportAcknowledgedUpdateForm
    )
    template_name: str = "cases/forms/report_acknowledged.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-12-week-update-requested", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseTwelveWeekUpdateRequestedUpdateView(CaseUpdateView):
    """
    View to update 12-week update requested
    """

    form_class: Type[CaseTwelveWeekUpdateRequestedUpdateForm] = (
        CaseTwelveWeekUpdateRequestedUpdateForm
    )
    template_name: str = "cases/forms/12_week_update_requested.html"

    def form_valid(self, form: CaseTwelveWeekUpdateRequestedUpdateForm):
        """
        Recalculate chaser dates if twelve week update requested date has changed;
        Otherwise set sent dates based on chaser date checkboxes.
        """
        self.object: Case = form.save(commit=False)
        if "twelve_week_update_requested_date" in form.changed_data:
            self.object = calculate_twelve_week_chaser_dates(
                case=self.object,
                twelve_week_update_requested_date=form.cleaned_data[
                    "twelve_week_update_requested_date"
                ],
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-12-week-one-week-followup-final",
                kwargs={"pk": self.object.id},
            )
        return super().get_success_url()


class CaseOneWeekFollowupFinalUpdateView(CaseUpdateView):
    """
    View to update One week followup for final update
    """

    form_class: Type[CaseOneWeekFollowupFinalUpdateForm] = (
        CaseOneWeekFollowupFinalUpdateForm
    )
    template_name: str = "cases/forms/12_week_one_week_followup_final.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-12-week-update-request-ack", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


class CaseTwelveWeekUpdateAcknowledgedUpdateView(CaseUpdateView):
    """
    View to update 12-week update request acknowledged
    """

    form_class: Type[CaseTwelveWeekUpdateAcknowledgedUpdateForm] = (
        CaseTwelveWeekUpdateAcknowledgedUpdateForm
    )
    template_name: str = "cases/forms/12_week_update_request_ack.html"

    def get_success_url(self) -> str:
        """
        Detect the submit button used and act accordingly.
        """
        if "save_continue" in self.request.POST:
            return reverse(
                "cases:edit-twelve-week-retest", kwargs={"pk": self.object.id}
            )
        return super().get_success_url()


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

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            return reverse("cases:edit-enforcement-recommendation", kwargs=case_pk)
        return super().get_success_url()


class CaseEnforcementRecommendationUpdateView(CaseUpdateView):
    """
    View to record the enforcement recommendation
    """

    form_class: Type[CaseEnforcementRecommendationUpdateForm] = (
        CaseEnforcementRecommendationUpdateForm
    )
    template_name: str = "cases/forms/enforcement_recommendation.html"

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

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get context data for template rendering"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = self.object
        equality_body_metadata_columns: List[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case, column_definitions=EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
            )
        )
        equality_body_report_columns: List[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case, column_definitions=EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
            )
        )
        equality_body_correspondence_columns: List[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case,
                column_definitions=EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_test_summary_columns: List[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case,
                column_definitions=EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
            )
        )
        all_equality_body_columns: List[EqualityBodyCSVColumn] = (
            equality_body_metadata_columns
            + equality_body_report_columns
            + equality_body_correspondence_columns
            + equality_body_test_summary_columns
        )
        required_data_missing_columns: List[EqualityBodyCSVColumn] = [
            column
            for column in all_equality_body_columns
            if column.required_data_missing
        ]
        context["equality_body_metadata_columns"] = equality_body_metadata_columns
        context["equality_body_report_columns"] = equality_body_report_columns
        context["equality_body_correspondence_columns"] = (
            equality_body_correspondence_columns
        )
        context["equality_body_test_summary_columns"] = (
            equality_body_test_summary_columns
        )
        context["required_data_missing_columns"] = required_data_missing_columns
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            if case.variant == Case.Variant.CLOSE_CASE:
                return reverse("cases:edit-statement-enforcement", kwargs=case_pk)
            else:
                return reverse("cases:edit-equality-body-metadata", kwargs=case_pk)
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


def export_feedback_suvey_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for feedback survey"""
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_feedback_survey_cases(cases=filter_cases(form=case_search_form))


class CaseStatementEnforcementUpdateView(CaseUpdateView):
    """
    View of statement enforcement
    """

    form_class: Type[CaseStatementEnforcementUpdateForm] = (
        CaseStatementEnforcementUpdateForm
    )
    template_name: str = "cases/forms/statement_enforcement.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case_pk: Dict[str, int] = {"pk": self.object.id}
            return reverse("cases:edit-equality-body-metadata", kwargs=case_pk)
        return super().get_success_url()


class CaseEqualityBodyMetadataUpdateView(CaseUpdateView):
    """
    View of equality body metadata
    """

    form_class: Type[CaseEqualityBodyMetadataUpdateForm] = (
        CaseEqualityBodyMetadataUpdateForm
    )
    template_name: str = "common/case_form.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            case: Case = self.object
            case_pk: Dict[str, int] = {"pk": case.id}
            return reverse("cases:list-equality-body-correspondence", kwargs=case_pk)
        return super().get_success_url()


class ListCaseEqualityBodyCorrespondenceUpdateView(CaseUpdateView):
    """
    View of equality body correspondence list
    """

    form_class: Type[ListCaseEqualityBodyCorrespondenceUpdateForm] = (
        ListCaseEqualityBodyCorrespondenceUpdateForm
    )
    template_name: str = "cases/forms/equality_body_correspondence_list.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case to context"""
        case: Case = self.object
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        view_url_param: Union[str, None] = self.request.GET.get("view")
        show_unresolved = view_url_param == "unresolved"
        context["show_unresolved"] = show_unresolved
        if show_unresolved:
            context["equality_body_correspondences"] = (
                case.equalitybodycorrespondence_set.filter(
                    status=EqualityBodyCorrespondence.Status.UNRESOLVED
                )
            )
        else:
            context["equality_body_correspondences"] = (
                case.equalitybodycorrespondence_set.all()
            )
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        equality_body_correspondence_id_to_toggle: Optional[int] = (
            get_id_from_button_name(
                button_name_prefix="toggle_status_",
                querydict=self.request.POST,
            )
        )
        if equality_body_correspondence_id_to_toggle is not None:
            equality_body_correspondence: EqualityBodyCorrespondence = (
                EqualityBodyCorrespondence.objects.get(
                    id=equality_body_correspondence_id_to_toggle
                )
            )
            if (
                equality_body_correspondence.status
                == EqualityBodyCorrespondence.Status.UNRESOLVED
            ):
                equality_body_correspondence.status = (
                    EqualityBodyCorrespondence.Status.RESOLVED
                )
            else:
                equality_body_correspondence.status = (
                    EqualityBodyCorrespondence.Status.UNRESOLVED
                )
            record_model_update_event(
                user=self.request.user, model_object=equality_body_correspondence
            )
            equality_body_correspondence.save()
        return super().form_valid(form)


class EqualityBodyCorrespondenceCreateView(CreateView):
    """
    View to create an equality body correspondence
    """

    model: Type[EqualityBodyCorrespondence] = EqualityBodyCorrespondence
    form_class: Type[EqualityBodyCorrespondenceCreateForm] = (
        EqualityBodyCorrespondenceCreateForm
    )
    template_name: str = "cases/forms/equality_body_correspondence_create.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case to context as object"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        context["object"] = case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        equality_body_correspondence: EqualityBodyCorrespondence = form.save(
            commit=False
        )
        case: Case = Case.objects.get(pk=self.kwargs["case_id"])
        equality_body_correspondence.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Record creation of object and return to equality body correspondence page"""
        record_model_create_event(user=self.request.user, model_object=self.object)
        if "save_return" in self.request.POST:
            return reverse(
                "cases:list-equality-body-correspondence",
                kwargs={"pk": self.object.case.id},
            )
        return reverse(
            "cases:edit-equality-body-correspondence", kwargs={"pk": self.object.id}
        )


class CaseEqualityBodyCorrespondenceUpdateView(UpdateView):
    """
    View of equality body metadata
    """

    model: Type[EqualityBodyCorrespondence] = EqualityBodyCorrespondence
    form_class: Type[EqualityBodyCorrespondenceCreateForm] = (
        EqualityBodyCorrespondenceCreateForm
    )
    context_object_name: str = "equality_body_correspondence"
    template_name: str = "cases/forms/equality_body_correspondence_update.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        equality_body_correspondence: EqualityBodyCorrespondence = form.save(
            commit=False
        )
        record_model_update_event(
            user=self.request.user, model_object=equality_body_correspondence
        )
        equality_body_correspondence.save()
        if "save_return" in self.request.POST:
            url: str = reverse(
                "cases:list-equality-body-correspondence",
                kwargs={"pk": self.object.case.id},
            )
        else:
            url: str = reverse(
                "cases:edit-equality-body-correspondence", kwargs={"pk": self.object.id}
            )
        return HttpResponseRedirect(url)


class CaseRetestOverviewTemplateView(CaseUpdateView):
    template_name: str = "cases/forms/retest_overview.html"
    fields = ["version"]

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add platform settings to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = self.object
        context["equality_body_retests"] = case.retests.filter(id_within_case__gt=0)
        return context


class CaseRetestCreateErrorTemplateView(TemplateView):
    template_name: str = "cases/retest_create_error.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add platform settings to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = get_object_or_404(Case, id=kwargs.get("pk"))
        context["case"] = case
        return context


class CaseLegacyEndOfCaseUpdateView(CaseUpdateView):
    """
    View to note correspondence with enforcement body
    """

    form_class: Type[CaseStatementEnforcementUpdateForm] = (
        CaseStatementEnforcementUpdateForm
    )
    template_name: str = "cases/forms/legacy_end_of_case.html"


class CaseZendeskTicketsDetailView(DetailView):
    """
    View of Zendesk tickets for a case
    """

    model: Type[Case] = Case
    context_object_name: str = "case"
    template_name: str = "cases/zendesk_tickets.html"


class ZendeskTicketCreateView(CreateView):
    """
    View to create a Zendesk ticket
    """

    model: Type[Case] = ZendeskTicket
    form_class: Type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    template_name: str = "cases/forms/zendesk_ticket_create.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case to context as object"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        context["object"] = case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: Case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        zendesk_ticket: ZendeskTicket = form.save(commit=False)
        zendesk_ticket.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        zendesk_ticket: ZendeskTicket = self.object
        user: User = self.request.user
        record_model_create_event(user=user, model_object=zendesk_ticket)
        case_pk: Dict[str, int] = {"pk": zendesk_ticket.case.id}
        return reverse("cases:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketUpdateView(UpdateView):
    """
    View to update Zendesk ticket
    """

    model: Type[ZendeskTicket] = ZendeskTicket
    form_class: Type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    context_object_name: str = "zendesk_ticket"
    template_name: str = "cases/forms/zendesk_ticket_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            zendesk_ticket: ZendeskTicket = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(user=user, model_object=zendesk_ticket)
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to zendesk tickets page on save"""
        zendesk_ticket: ZendeskTicket = self.object
        case_pk: Dict[str, int] = {"pk": zendesk_ticket.case.id}
        return reverse("cases:zendesk-tickets", kwargs=case_pk)


def delete_zendesk_ticket(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Delete ZendeskTicket

    Args:
        request (HttpRequest): Django HttpRequest
        pk (int): Id of ZendeskTicket to delete

    Returns:
        HttpResponse: Django HttpResponse
    """
    zendesk_ticket: ZendeskTicket = get_object_or_404(ZendeskTicket, id=pk)
    zendesk_ticket.is_deleted = True
    record_model_update_event(user=request.user, model_object=zendesk_ticket)
    zendesk_ticket.save()
    return redirect(
        reverse("cases:zendesk-tickets", kwargs={"pk": zendesk_ticket.case.id})
    )


class CaseEmailTemplateListView(ListView):
    """
    View of list of email templates for the case.
    """

    model: Type[EmailTemplate] = EmailTemplate
    template_name: str = "cases/emails/template_list.html"
    context_object_name: str = "email_templates"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add current case to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        self.case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        context["case"] = self.case
        return context


class CaseEmailTemplatePreviewDetailView(DetailView):
    """
    View email template populated with case data
    """

    model: Type[EmailTemplate] = EmailTemplate
    template_name: str = "cases/emails/template_preview.html"
    context_object_name: str = "email_template"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add case and email template to context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        self.case = get_object_or_404(Case, id=self.kwargs.get("case_id"))
        context["12_weeks_from_today"] = date.today() + timedelta(
            days=TWELVE_WEEKS_IN_DAYS
        )
        context["case"] = self.case
        context["retest"] = self.case.retests.first()
        if self.case.audit is not None:
            context["issues_tables"] = build_issues_tables(
                pages=self.case.audit.testable_pages,
                check_results_attr="unfixed_check_results",
            )
            context["retest_issues_tables"] = build_issues_tables(
                pages=self.case.audit.retestable_pages,
                use_retest_notes=True,
                check_results_attr="unfixed_check_results",
            )
        context["email_template_render"] = self.object.render(context=context)
        return context


def enable_correspondence_process(
    request: HttpRequest, pk: int
) -> HttpResponseRedirect:
    """Mark correspondence process as enabled in Case"""
    case: Case = get_object_or_404(Case, id=pk)
    case.enable_correspondence_process = True
    case.save()
    return redirect(
        reverse("cases:edit-request-contact-details", kwargs={"pk": case.id})
    )
