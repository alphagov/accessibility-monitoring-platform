"""
Views for cases app
"""

from datetime import date, timedelta
from typing import Any

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

from ..audits.utils import get_audit_summary_context, report_data_updated
from ..cases.forms import CaseSearchForm
from ..comments.models import Comment
from ..comments.utils import add_comment_notification
from ..common.email_template_utils import get_email_template_context
from ..common.mark_deleted_util import get_id_from_button_name
from ..common.models import EmailTemplate
from ..common.sitemap import PlatformPage, Sitemap, get_platform_page_by_url_name
from ..common.utils import amp_format_date, extract_domain_from_url
from ..common.views import (
    HideCaseNavigationMixin,
    NextPlatformPageMixin,
    ShowGoBackJSWidgetMixin,
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
from ..notifications.utils import add_task, mark_tasks_as_read
from ..reports.utils import publish_report_util
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
    CaseQAApprovalUpdateForm,
    CaseQAAuditorUpdateForm,
    CaseQACommentsUpdateForm,
    CaseReportAcknowledgedUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportFourWeekFollowupUpdateForm,
    CaseReportOneWeekFollowupUpdateForm,
    CaseReportReadyForQAUpdateForm,
    CaseReportSentOnUpdateForm,
    CaseRequestContactDetailsUpdateForm,
    CaseReviewChangesUpdateForm,
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
    ZendeskTicketConfirmDeleteUpdateForm,
    ZendeskTicketCreateUpdateForm,
)
from .models import (
    ONE_WEEK_IN_DAYS,
    Contact,
    EqualityBodyCorrespondence,
    SimplifiedCase,
    SimplifiedEventHistory,
    ZendeskTicket,
)
from .utils import (
    filter_cases,
    get_case_detail_sections,
    record_case_event,
    record_model_create_event,
    record_model_update_event,
    replace_search_key_with_case_search,
)

FOUR_WEEKS_IN_DAYS: int = 4 * ONE_WEEK_IN_DAYS
TWELVE_WEEKS_IN_DAYS: int = 12 * ONE_WEEK_IN_DAYS
TRUTHY_SEARCH_FIELDS: list[str] = [
    "sort_by",
    "status",
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
]
REMOVE_CONTACT_BUTTON_PREFIX: str = "remove_contact_"


def find_duplicate_cases(
    url: str, organisation_name: str = ""
) -> QuerySet[SimplifiedCase]:
    """Look for cases with matching domain or organisation name"""
    domain: str = extract_domain_from_url(url)
    if organisation_name:
        return SimplifiedCase.objects.filter(
            Q(organisation_name__icontains=organisation_name) | Q(domain=domain)
        )
    return SimplifiedCase.objects.filter(domain=domain)


def calculate_report_followup_dates(
    case: SimplifiedCase, report_sent_date: date
) -> SimplifiedCase:
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
    case: SimplifiedCase, seven_day_no_contact_email_sent_date: date
) -> SimplifiedCase:
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
    case: SimplifiedCase, twelve_week_update_requested_date: date
) -> SimplifiedCase:
    """Calculate chaser dates based on a twelve week update requested date"""
    if twelve_week_update_requested_date is None:
        case.twelve_week_1_week_chaser_due_date = None
    else:
        case.twelve_week_1_week_chaser_due_date = (
            twelve_week_update_requested_date + timedelta(days=ONE_WEEK_IN_DAYS)
        )
    return case


def format_due_date_help_text(due_date: date | None) -> str:
    """Format date and prefix with 'Due' if present"""
    if due_date is None:
        return "None"
    return f"Due {amp_format_date(due_date)}"


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case detail sections to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        case: SimplifiedCase = self.object
        sitemap: Sitemap = Sitemap(request=self.request)

        return {
            **{
                "case_detail_sections": get_case_detail_sections(
                    case=case, sitemap=sitemap
                )
            },
            **context,
        }


class CaseSearchView(CaseDetailView):
    """
    View and search details of a single case
    """

    template_name: str = "cases/case_search_all_data.html"


class CaseCreateView(ShowGoBackJSWidgetMixin, CreateView):
    """
    View to create a case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    form_class: type[CaseCreateForm] = CaseCreateForm
    context_object_name: str = "case"
    template_name: str = "simplified/forms/create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            simplified_case: SimplifiedCase = form.save(commit=False)
            simplified_case.created_by = self.request.user
            simplified_case.test_type = SimplifiedCase.TestType.SIMPLIFIED
            return super().form_valid(form)

        context: dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[SimplifiedCase] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)

        simplified_case: SimplifiedCase = form.save(commit=False)
        simplified_case.created_by = self.request.user
        simplified_case.test_type = SimplifiedCase.TestType.SIMPLIFIED
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        case: SimplifiedCase = self.object
        user: User = self.request.user
        record_model_create_event(user=user, model_object=case, case=case)
        record_case_event(user=user, new_case=case)
        case_pk: dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("simplified:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("simplified:case-create")
        elif "save_exit" in self.request.POST:
            url: str = reverse("cases:case-list")
        else:
            url: str = reverse("simplified:manage-contact-details", kwargs=case_pk)
        return url


class CaseUpdateView(NextPlatformPageMixin, UpdateView):
    """
    View to update case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "common/case_form.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: SimplifiedCase = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(
                user=user, model_object=self.object, case=self.object
            )
            old_case: SimplifiedCase = SimplifiedCase.objects.get(pk=self.object.id)
            old_status: str = old_case.status
            record_case_event(user=user, new_case=self.object, old_case=old_case)

            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)

            self.object.save()

            if old_status != self.object.status:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    f"Status changed from '{old_case.get_status_display()}'"
                    f" to '{self.object.status.get_status_display()}'",
                )
        return HttpResponseRedirect(self.get_success_url())


class CaseMetadataUpdateView(CaseUpdateView):
    """
    View to update case metadata
    """

    form_class: type[CaseMetadataUpdateForm] = CaseMetadataUpdateForm

    def get_next_platform_page(self) -> PlatformPage:
        case: SimplifiedCase = self.object
        next_page_url_name: str = (
            "audits:edit-audit-metadata"
            if case.audit is not None
            else "cases:edit-test-results"
        )
        return get_platform_page_by_url_name(url_name=next_page_url_name, instance=case)

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: SimplifiedCase = self.object
        if case.published_report_url:
            if (
                "enforcement_body" in form.changed_data
                or "home_page_url" in form.changed_data
                or "organisation_name" in form.changed_data
            ):
                report_data_updated(audit=case.audit)
        return super().form_valid(form=form)


class CaseTestResultsUpdateView(CaseUpdateView):
    """
    View to update case test results
    """

    form_class: type[CaseTestResultsUpdateForm] = CaseTestResultsUpdateForm
    template_name: str = "cases/forms/test_results.html"


class CaseCreateReportUpdateView(DetailView):
    """
    View to create the report for this case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    form_class: type[CaseReportDetailsUpdateForm] = CaseReportDetailsUpdateForm
    template_name: str = "cases/forms/report_create.html"


class CaseReportReadyForQAUpdateView(CaseUpdateView):
    """
    View to update case report details
    """

    model: type[SimplifiedCase] = SimplifiedCase
    form_class: type[CaseReportReadyForQAUpdateForm] = CaseReportReadyForQAUpdateForm
    template_name: str = "cases/forms/report_ready_for_qa.html"


class CaseQAAuditorUpdateView(CaseUpdateView):
    """
    View to record QA auditor
    """

    form_class: type[CaseQAAuditorUpdateForm] = CaseQAAuditorUpdateForm
    template_name: str = "cases/forms/qa_auditor.html"


class CaseQACommentsUpdateView(CaseUpdateView):
    """
    View to update QA comments page
    """

    form_class: type[CaseQACommentsUpdateForm] = CaseQACommentsUpdateForm
    template_name: str = "cases/forms/qa_comments.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: SimplifiedCase = self.object
        body: str = form.cleaned_data.get("body")
        if body:
            comment: Comment = Comment.objects.create(
                case=case, user=self.request.user, body=form.cleaned_data.get("body")
            )
            record_model_create_event(
                user=self.request.user, model_object=comment, case=case
            )
            add_comment_notification(self.request, comment)
        return HttpResponseRedirect(self.get_success_url())


class CaseQAApprovalUpdateView(CaseUpdateView):
    """
    View to record QA approval
    """

    form_class: type[CaseQAApprovalUpdateForm] = CaseQAApprovalUpdateForm
    template_name: str = "cases/forms/qa_approval.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Notify auditor if case has been QA approved."""
        if form.changed_data and "report_approved_status" in form.changed_data:
            if (
                self.object.report_approved_status
                == SimplifiedCase.ReportApprovedStatus.APPROVED
            ):
                case: SimplifiedCase = self.object
                if case.auditor:
                    task: Task = add_task(
                        user=case.auditor,
                        case=case,
                        type=Task.Type.REPORT_APPROVED,
                        description=f"{self.request.user.get_full_name()} QA approved Case {case}",
                        list_description=f"{case} - Report approved",
                        request=self.request,
                    )
                    record_model_create_event(
                        user=self.request.user, model_object=task, case=case
                    )
        return super().form_valid(form=form)


class CasePublishReportUpdateView(CaseUpdateView):
    """
    View to publish report after QA approval
    """

    form_class: type[CasePublishReportUpdateForm] = CasePublishReportUpdateForm
    template_name: str = "cases/forms/publish_report.html"

    def form_valid(self, form: ModelForm):
        """Publish report if requested"""
        case: SimplifiedCase = self.object
        if "create_html_report" in self.request.POST:
            publish_report_util(report=case.report, request=self.request)
        return super().form_valid(form)


class ManageContactDetailsUpdateView(CaseUpdateView):
    """
    View to list case contacts
    """

    form_class: type[ManageContactDetailsUpdateForm] = ManageContactDetailsUpdateForm
    template_name: str = "cases/forms/manage_contact_details.html"

    def get_next_platform_page(self) -> PlatformPage:
        case: SimplifiedCase = self.object
        next_page_url_name: str = (
            "cases:edit-request-contact-details"
            if case.enable_correspondence_process is True
            else "cases:edit-report-sent-on"
        )
        return get_platform_page_by_url_name(url_name=next_page_url_name, instance=case)


class ContactCreateView(CreateView):
    """
    View to create case contact
    """

    model: type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: type[ContactCreateForm] = ContactCreateForm
    template_name: str = "cases/forms/contact_create.html"

    def form_valid(self, form: ContactCreateForm):
        """Populate case of contact"""
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        contact: Contact = form.save(commit=False)
        contact.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        case_pk: dict[str, int] = {"pk": case.id}
        return reverse("cases:manage-contact-details", kwargs=case_pk)


class ContactUpdateView(UpdateView):
    """
    View to create case contact
    """

    model: type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: type[ContactUpdateForm] = ContactUpdateForm
    template_name: str = "cases/forms/contact_update.html"

    def form_valid(self, form: ContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        contact: Contact = form.save(commit=False)
        if "delete_contact" in self.request.POST:
            contact.is_deleted = True
        record_model_update_event(
            user=self.request.user, model_object=contact, case=contact.case
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        case_pk: dict[str, int] = {"pk": self.object.case.id}
        return reverse("cases:manage-contact-details", kwargs=case_pk)


class CaseRequestContactDetailsUpdateView(CaseUpdateView):
    """
    View to update Request contact details
    """

    form_class: type[CaseRequestContactDetailsUpdateForm] = (
        CaseRequestContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/request_initial_contact.html"

    def form_valid(self, form: CaseReportSentOnUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: SimplifiedCase = form.save(commit=False)
        if "seven_day_no_contact_email_sent_date" in form.changed_data:
            self.object = calculate_no_contact_chaser_dates(
                case=self.object,
                seven_day_no_contact_email_sent_date=form.cleaned_data[
                    "seven_day_no_contact_email_sent_date"
                ],
            )
        return super().form_valid(form)


class CaseOneWeekContactDetailsUpdateView(CaseUpdateView):
    """
    View to update One week contact details
    """

    form_class: type[CaseOneWeekContactDetailsUpdateForm] = (
        CaseOneWeekContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/one_week_followup_contact.html"


class CaseFourWeekContactDetailsUpdateView(CaseUpdateView):
    """
    View to update Four week contact details
    """

    form_class: type[CaseFourWeekContactDetailsUpdateForm] = (
        CaseFourWeekContactDetailsUpdateForm
    )
    template_name: str = "cases/forms/four_week_followup_contact.html"


class CaseNoPSBResponseUpdateView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, CaseUpdateView
):
    """
    View to set no psb contact flag
    """

    form_class: type[CaseNoPSBContactUpdateForm] = CaseNoPSBContactUpdateForm
    template_name: str = "cases/forms/no_psb_response.html"


class CaseReportSentOnUpdateView(CaseUpdateView):
    """
    View to update Report sent on
    """

    form_class: type[CaseReportSentOnUpdateForm] = CaseReportSentOnUpdateForm
    template_name: str = "cases/forms/report_sent_on.html"

    def form_valid(self, form: CaseReportSentOnUpdateForm):
        """
        Recalculate followup dates if report sent date has changed;
        Otherwise set sent dates based on followup date checkboxes.
        """
        self.object: SimplifiedCase = form.save(commit=False)
        if "report_sent_date" in form.changed_data:
            self.object = calculate_report_followup_dates(
                case=self.object, report_sent_date=form.cleaned_data["report_sent_date"]
            )
        return super().form_valid(form)


class CaseReportOneWeekFollowupUpdateView(CaseUpdateView):
    """
    View to update One week followup
    """

    form_class: type[CaseReportOneWeekFollowupUpdateForm] = (
        CaseReportOneWeekFollowupUpdateForm
    )
    template_name: str = "cases/forms/report_one_week_followup.html"


class CaseReportFourWeekFollowupUpdateView(CaseUpdateView):
    """
    View to update Four week followup
    """

    form_class: type[CaseReportFourWeekFollowupUpdateForm] = (
        CaseReportFourWeekFollowupUpdateForm
    )
    template_name: str = "cases/forms/report_four_week_followup.html"


class CaseReportAcknowledgedUpdateView(CaseUpdateView):
    """
    View to update Report acknowledged
    """

    form_class: type[CaseReportAcknowledgedUpdateForm] = (
        CaseReportAcknowledgedUpdateForm
    )
    template_name: str = "cases/forms/report_acknowledged.html"


class CaseTwelveWeekUpdateRequestedUpdateView(CaseUpdateView):
    """
    View to update 12-week update requested
    """

    form_class: type[CaseTwelveWeekUpdateRequestedUpdateForm] = (
        CaseTwelveWeekUpdateRequestedUpdateForm
    )
    template_name: str = "cases/forms/12_week_update_requested.html"

    def form_valid(self, form: CaseTwelveWeekUpdateRequestedUpdateForm):
        """
        Recalculate chaser dates if twelve week update requested date has changed;
        Otherwise set sent dates based on chaser date checkboxes.
        """
        self.object: SimplifiedCase = form.save(commit=False)
        if "twelve_week_update_requested_date" in form.changed_data:
            self.object = calculate_twelve_week_chaser_dates(
                case=self.object,
                twelve_week_update_requested_date=form.cleaned_data[
                    "twelve_week_update_requested_date"
                ],
            )
        return super().form_valid(form)


class CaseOneWeekFollowupFinalUpdateView(CaseUpdateView):
    """
    View to update One week followup for final update
    """

    form_class: type[CaseOneWeekFollowupFinalUpdateForm] = (
        CaseOneWeekFollowupFinalUpdateForm
    )
    template_name: str = "cases/forms/12_week_one_week_followup_final.html"


class CaseTwelveWeekUpdateAcknowledgedUpdateView(CaseUpdateView):
    """
    View to update 12-week update request acknowledged
    """

    form_class: type[CaseTwelveWeekUpdateAcknowledgedUpdateForm] = (
        CaseTwelveWeekUpdateAcknowledgedUpdateForm
    )
    template_name: str = "cases/forms/12_week_update_request_ack.html"

    def get_next_platform_page(self) -> PlatformPage:
        case: SimplifiedCase = self.object
        if case.audit:
            if case.show_start_12_week_retest:
                return get_platform_page_by_url_name(
                    url_name="cases:edit-twelve-week-retest", instance=case
                )
            else:
                return get_platform_page_by_url_name(
                    url_name="audits:edit-audit-retest-metadata",
                    instance=case.audit,
                )
        return get_platform_page_by_url_name(
            url_name="cases:edit-review-changes", instance=case
        )


class CaseTwelveWeekRetestUpdateView(CaseUpdateView):
    """
    View to update case twelve week retest results
    """

    form_class: type[CaseTwelveWeekRetestUpdateForm] = CaseTwelveWeekRetestUpdateForm
    template_name: str = "cases/forms/twelve_week_retest.html"


class CaseReviewChangesUpdateView(CaseUpdateView):
    """
    View to record review of changes made by PSB
    """

    form_class: type[CaseReviewChangesUpdateForm] = CaseReviewChangesUpdateForm
    template_name: str = "cases/forms/review_changes.html"


class CaseEnforcementRecommendationUpdateView(CaseUpdateView):
    """
    View to record the enforcement recommendation
    """

    form_class: type[CaseEnforcementRecommendationUpdateForm] = (
        CaseEnforcementRecommendationUpdateForm
    )
    template_name: str = "cases/forms/enforcement_recommendation.html"


class CaseCloseUpdateView(CaseUpdateView):
    """
    View to record sending the compliance decision
    """

    form_class: type[CaseCloseUpdateForm] = CaseCloseUpdateForm
    template_name: str = "cases/forms/case_close.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = self.object
        equality_body_metadata_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case, column_definitions=EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT
            )
        )
        equality_body_report_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case, column_definitions=EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT
            )
        )
        equality_body_correspondence_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case,
                column_definitions=EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_test_summary_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=case,
                column_definitions=EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
            )
        )
        all_equality_body_columns: list[EqualityBodyCSVColumn] = (
            equality_body_metadata_columns
            + equality_body_report_columns
            + equality_body_correspondence_columns
            + equality_body_test_summary_columns
        )
        required_data_missing_columns: list[EqualityBodyCSVColumn] = [
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


class PostCaseUpdateView(CaseUpdateView):
    """
    View to record post case notes
    """

    form_class: type[PostCaseUpdateForm] = PostCaseUpdateForm
    template_name: str = "cases/forms/post_case.html"

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_exit" in self.request.POST:
            case_pk: dict[str, int] = {"pk": self.object.id}
            return reverse("cases:case-detail", kwargs=case_pk)
        return super().get_success_url()


class CaseDeactivateUpdateView(CaseUpdateView):
    """
    View to deactivate case
    """

    form_class: type[CaseDeactivateForm] = CaseDeactivateForm
    template_name: str = "cases/forms/deactivate.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: SimplifiedCase = form.save(commit=False)
        case.is_deactivated = True
        case.deactivate_date = date.today()
        record_model_update_event(user=self.request.user, model_object=case, case=case)
        case.save()
        return HttpResponseRedirect(case.get_absolute_url())


class CaseReactivateUpdateView(CaseUpdateView):
    """
    View to reactivate case
    """

    form_class: type[CaseDeactivateForm] = CaseDeactivateForm
    template_name: str = "cases/forms/reactivate.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: SimplifiedCase = form.save(commit=False)
        case.is_deactivated = False
        record_model_update_event(user=self.request.user, model_object=case, case=case)
        case.save()
        return HttpResponseRedirect(case.get_absolute_url())


class CaseStatusWorkflowDetailView(DetailView):
    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "cases/status_workflow.html"


class CaseOutstandingIssuesDetailView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, DetailView
):
    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "cases/outstanding_issues.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = self.object
        if case.audit is not None:
            return {
                **context,
                **get_audit_summary_context(request=self.request, audit=case.audit),
            }
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

    form_class: type[CaseStatementEnforcementUpdateForm] = (
        CaseStatementEnforcementUpdateForm
    )
    template_name: str = "cases/forms/statement_enforcement.html"


class CaseEqualityBodyMetadataUpdateView(CaseUpdateView):
    """
    View of equality body metadata
    """

    form_class: type[CaseEqualityBodyMetadataUpdateForm] = (
        CaseEqualityBodyMetadataUpdateForm
    )
    template_name: str = "common/case_form.html"


class ListCaseEqualityBodyCorrespondenceUpdateView(CaseUpdateView):
    """
    View of equality body correspondence list
    """

    form_class: type[ListCaseEqualityBodyCorrespondenceUpdateForm] = (
        ListCaseEqualityBodyCorrespondenceUpdateForm
    )
    template_name: str = "cases/forms/equality_body_correspondence_list.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context"""
        case: SimplifiedCase = self.object
        context: dict[str, Any] = super().get_context_data(**kwargs)
        view_url_param: str | None = self.request.GET.get("view")
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
        equality_body_correspondence_id_to_toggle: int | None = get_id_from_button_name(
            button_name_prefix="toggle_status_",
            querydict=self.request.POST,
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
                user=self.request.user,
                model_object=equality_body_correspondence,
                case=equality_body_correspondence.case,
            )
            equality_body_correspondence.save()
        return super().form_valid(form)


class EqualityBodyCorrespondenceCreateView(CreateView):
    """
    View to create an equality body correspondence
    """

    model: type[EqualityBodyCorrespondence] = EqualityBodyCorrespondence
    form_class: type[EqualityBodyCorrespondenceCreateForm] = (
        EqualityBodyCorrespondenceCreateForm
    )
    template_name: str = "cases/forms/equality_body_correspondence_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context as object"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        context["object"] = case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        equality_body_correspondence: EqualityBodyCorrespondence = form.save(
            commit=False
        )
        case: SimplifiedCase = SimplifiedCase.objects.get(pk=self.kwargs["case_id"])
        equality_body_correspondence.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Record creation of object and return to equality body correspondence page"""
        record_model_create_event(
            user=self.request.user, model_object=self.object, case=self.object.case
        )
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

    model: type[EqualityBodyCorrespondence] = EqualityBodyCorrespondence
    form_class: type[EqualityBodyCorrespondenceCreateForm] = (
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
            user=self.request.user,
            model_object=equality_body_correspondence,
            case=equality_body_correspondence.case,
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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add platform settings to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = self.object
        context["equality_body_retests"] = case.retests.filter(id_within_case__gt=0)
        return context


class CaseRetestCreateErrorTemplateView(TemplateView):
    template_name: str = "cases/retest_create_error.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add platform settings to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = get_object_or_404(SimplifiedCase, id=kwargs.get("pk"))
        context["case"] = case
        return context


class CaseZendeskTicketsDetailView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, DetailView
):
    """
    View of Zendesk tickets for a case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "cases/zendesk_tickets.html"


class ZendeskTicketCreateView(HideCaseNavigationMixin, CreateView):
    """
    View to create a Zendesk ticket
    """

    model: type[SimplifiedCase] = ZendeskTicket
    form_class: type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    template_name: str = "cases/forms/zendesk_ticket_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context as object"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        context["object"] = case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        zendesk_ticket: ZendeskTicket = form.save(commit=False)
        zendesk_ticket.case = case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        zendesk_ticket: ZendeskTicket = self.object
        user: User = self.request.user
        record_model_create_event(
            user=user, model_object=zendesk_ticket, case=zendesk_ticket.case
        )
        case_pk: dict[str, int] = {"pk": zendesk_ticket.case.id}
        return reverse("cases:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketUpdateView(HideCaseNavigationMixin, UpdateView):
    """
    View to update Zendesk ticket
    """

    model: type[ZendeskTicket] = ZendeskTicket
    form_class: type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    context_object_name: str = "zendesk_ticket"
    template_name: str = "cases/forms/zendesk_ticket_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add update event"""
        if form.changed_data:
            zendesk_ticket: ZendeskTicket = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(
                user=user, model_object=zendesk_ticket, case=zendesk_ticket.case
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to zendesk tickets page on save"""
        zendesk_ticket: ZendeskTicket = self.object
        case_pk: dict[str, int] = {"pk": zendesk_ticket.case.id}
        return reverse("cases:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketConfirmDeleteUpdateView(ZendeskTicketUpdateView):
    """
    View to confirm delete of Zendesk ticket
    """

    form_class: type[ZendeskTicketConfirmDeleteUpdateForm] = (
        ZendeskTicketConfirmDeleteUpdateForm
    )
    template_name: str = "cases/forms/zendesk_ticket_confirm_delete.html"


class CaseEmailTemplateListView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, ListView
):
    """
    View of list of email templates for the case.
    """

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "cases/emails/template_list.html"
    context_object_name: str = "email_templates"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add current case to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        self.case = get_object_or_404(SimplifiedCase, id=self.kwargs.get("case_id"))
        context["case"] = self.case
        return context

    def get_queryset(self) -> QuerySet[SimplifiedCase]:
        """Add filters to queryset"""
        return EmailTemplate.objects.filter(is_deleted=False)


class CaseEmailTemplatePreviewDetailView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, DetailView
):
    """
    View email template populated with case data
    """

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "cases/emails/template_preview.html"
    context_object_name: str = "email_template"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case and email template to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = get_object_or_404(
            SimplifiedCase, id=self.kwargs.get("case_id")
        )
        extra_context: dict[str, Any] = get_email_template_context(case=case)
        context["email_template_name"] = (
            f"common/emails/templates/{self.object.template_name}.html"
        )
        return {**extra_context, **context}


class CaseHistoryDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[SimplifiedCase] = SimplifiedCase
    context_object_name: str = "case"
    template_name: str = "cases/case_history.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add current case to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: SimplifiedCase = self.object
        event_history: SimplifiedEventHistory = SimplifiedEventHistory.objects.filter(
            case=case
        ).prefetch_related("parent")
        context["event_history"] = event_history
        context["all_users"] = User.objects.all().order_by("id")
        return context


def enable_correspondence_process(
    request: HttpRequest, pk: int
) -> HttpResponseRedirect:
    """Mark correspondence process as enabled in Case"""
    case: SimplifiedCase = get_object_or_404(SimplifiedCase, id=pk)
    case.enable_correspondence_process = True
    case.save()
    return redirect(
        reverse("cases:edit-request-contact-details", kwargs={"pk": case.id})
    )


def mark_qa_comments_as_read(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark QA comment reminders as read for the current user"""
    case: SimplifiedCase = SimplifiedCase.objects.get(id=pk)
    mark_tasks_as_read(user=request.user, case=case, type=Task.Type.QA_COMMENT)
    mark_tasks_as_read(user=request.user, case=case, type=Task.Type.REPORT_APPROVED)
    messages.success(request, f"{case} comments marked as read")
    return redirect(reverse("cases:edit-qa-comments", kwargs={"pk": case.id}))
