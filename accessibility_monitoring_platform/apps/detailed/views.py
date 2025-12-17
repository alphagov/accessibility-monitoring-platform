"""
Views for cases app
"""

from datetime import date, timedelta
from typing import Any

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..cases.csv_export import populate_equality_body_columns
from ..cases.forms import CaseSearchForm
from ..cases.models import BaseCase, TestType
from ..cases.utils import filter_cases, find_duplicate_cases
from ..comments.models import Comment
from ..comments.utils import add_comment_notification
from ..common.csv_export import EqualityBodyCSVColumn
from ..common.models import EmailTemplate
from ..common.sitemap import Sitemap
from ..common.utils import (
    add_12_weeks_to_date,
    extract_domain_from_url,
    get_detailed_mobile_email_template_context,
    replace_search_key_with_case_search,
)
from ..common.views import (
    HideCaseNavigationMixin,
    NextPlatformPageMixin,
    ShowGoBackJSWidgetMixin,
)
from ..notifications.models import Task
from ..notifications.utils import mark_tasks_as_read
from .csv_export import (
    DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from .forms import (
    DetailedCaseCloseUpdateForm,
    DetailedCaseCreateForm,
    DetailedCaseHistoryCreateForm,
    DetailedCaseHistoryUpdateForm,
    DetailedCaseMetadataUpdateForm,
    DetailedCaseRecommendationUpdateForm,
    DetailedCaseStatusUpdateForm,
    DetailedContactCreateForm,
    DetailedContactInformationRequestUpdateForm,
    DetailedContactUpdateForm,
    DetailedEnforcementBodyMetadataUpdateForm,
    DetailedFinalReportUpdateForm,
    DetailedInitialTestingDetailsUpdateForm,
    DetailedInitialTestingOutcomeUpdateForm,
    DetailedManageContactsUpdateForm,
    DetailedQAApprovalUpdateForm,
    DetailedQAAuditorUpdateForm,
    DetailedQACommentsUpdateForm,
    DetailedReportAcknowledgedUpdateForm,
    DetailedReportReadyForQAUpdateForm,
    DetailedReportSentUpdateForm,
    DetailedRetestComplianceDecisionsUpdateForm,
    DetailedRetestResultUpdateForm,
    DetailedStatementEnforcementUpdateForm,
    DetailedTwelveWeekDeadlineUpdateForm,
    DetailedTwelveWeekReceivedUpdateForm,
    DetailedTwelveWeekRequestUpdateForm,
    DetailedUnresponsivePSBUpdateForm,
    DetailedZendeskTicketConfirmDeleteUpdateForm,
    DetailedZendeskTicketCreateUpdateForm,
)
from .models import (
    Contact,
    DetailedCase,
    DetailedCaseHistory,
    DetailedEventHistory,
    ZendeskTicket,
)
from .utils import (
    add_to_detailed_case_history,
    download_detailed_cases,
    download_detailed_equality_body_cases,
    download_detailed_feedback_survey_cases,
    get_detailed_case_detail_sections,
    record_detailed_model_create_event,
    record_detailed_model_update_event,
)


class AddDetailedCaseToContextMixin:
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add detailed case into context"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["detailed_case"] = detailed_case
        return context


class MessageOnSaveMixin:
    def get_success_url(self) -> str:
        messages.add_message(
            self.request,
            messages.INFO,
            "Page saved",
        )
        return super().get_success_url()


class DetailedCaseCreateView(ShowGoBackJSWidgetMixin, CreateView):
    """
    View to create a case
    """

    model: type[DetailedCase] = DetailedCase
    form_class: type[DetailedCaseCreateForm] = DetailedCaseCreateForm
    context_object_name: str = "detailed_case"
    template_name: str = "cases/forms/create.html"

    def form_valid(self, form: DetailedCaseCreateForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            detailed_case: DetailedCase = form.save(commit=False)
            detailed_case.created_by = self.request.user
            detailed_case.test_type = DetailedCase.TestType.DETAILED
            return super().form_valid(form)

        context: dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[BaseCase] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)

        detailed_case: DetailedCase = form.save(commit=False)
        detailed_case.created_by = self.request.user
        detailed_case.test_type = DetailedCase.TestType.DETAILED
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        detailed_case: DetailedCase = self.object
        user: User = self.request.user
        record_detailed_model_create_event(
            user=user, model_object=detailed_case, detailed_case=detailed_case
        )
        DetailedCaseHistory.objects.create(
            detailed_case=detailed_case,
            event_type=DetailedCaseHistory.EventType.STATUS,
            value=detailed_case.get_status_display(),
            created_by=self.request.user,
        )
        case_pk: dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("detailed:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("detailed:case-create")
        else:
            url: str = reverse("cases:case-list")
        return url


class DetailedCaseDetailView(DetailView):
    """View of details of a single detailed Case"""

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "detailed_case"


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "detailed_case"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case detail sections to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        detailed_case: DetailedCase = self.object
        sitemap: Sitemap = Sitemap(request=self.request)

        return {
            **{
                "case_detail_sections": get_detailed_case_detail_sections(
                    detailed_case=detailed_case, sitemap=sitemap
                )
            },
            **context,
        }


class CaseSearchView(HideCaseNavigationMixin, CaseDetailView):
    """
    View and search details of a single case
    """

    template_name: str = "detailed/case_search_all_data.html"


class DetailedCaseUpdateView(NextPlatformPageMixin, UpdateView):
    """View to update DetailedCase"""

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "detailed_case"
    template_name: str = "detailed/base.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of detailed case"""
        if form.changed_data:
            self.object: DetailedCase = form.save(commit=False)
            user: User = self.request.user
            record_detailed_model_update_event(
                user=user, model_object=self.object, detailed_case=self.object
            )
            self.object.save()
            if "status" in form.changed_data:
                add_to_detailed_case_history(
                    detailed_case=self.object,
                    user=self.request.user,
                    value=self.object.get_status_display(),
                    event_type=DetailedCaseHistory.EventType.STATUS,
                )

        return HttpResponseRedirect(self.get_success_url())


class DetailedCaseMetadataUpdateView(DetailedCaseUpdateView):
    """View to update detailed case metadata"""

    form_class: type[DetailedCaseMetadataUpdateForm] = DetailedCaseMetadataUpdateForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: DetailedCase = form.save(commit=False)
            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)
        return super().form_valid(form)


class DetailedCaseStatusUpdateView(HideCaseNavigationMixin, DetailedCaseUpdateView):
    """View to update detailed case status"""

    model: type[DetailedCase] = DetailedCase
    form_class: type[DetailedCaseStatusUpdateForm] = DetailedCaseStatusUpdateForm
    context_object_name: str = "detailed_case"
    template_name: str = "detailed/forms/case_status.html"


class DetailedCaseNoteCreateView(HideCaseNavigationMixin, CreateView):
    """View to add a note to the DetailedCaseHistory"""

    model: type[DetailedCaseHistory] = DetailedCaseHistory
    form_class: type[DetailedCaseHistoryCreateForm] = DetailedCaseHistoryCreateForm
    context_object_name: str = "detailed_case_history"
    template_name: str = "detailed/forms/note_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["detailed_case"] = detailed_case
        context["detailed_case_history"] = detailed_case.detailedcasehistory_set.all()
        return context

    def form_valid(self, form: DetailedCaseHistoryCreateForm):
        """Process contents of valid form"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        detailed_case_history: DetailedCaseHistory = form.save(commit=False)
        detailed_case_history.detailed_case = detailed_case
        detailed_case_history.created_by = self.request.user
        detailed_case_history.label = detailed_case.get_status_display()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        detailed_case_history: DetailedCaseHistory = self.object
        detailed_case: DetailedCase = detailed_case_history.detailed_case
        user: User = self.request.user
        record_detailed_model_create_event(
            user=user,
            model_object=detailed_case_history,
            detailed_case=detailed_case,
        )
        return reverse(
            "detailed:create-case-note", kwargs={"case_id": detailed_case.id}
        )


class DetailedCaseNoteUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to edit a note on the DetailedCaseHistory"""

    model: type[DetailedCaseHistory] = DetailedCaseHistory
    form_class: type[DetailedCaseHistoryUpdateForm] = DetailedCaseHistoryUpdateForm
    context_object_name: str = "detailed_case_history"
    template_name: str = "detailed/forms/note_update.html"

    def form_valid(self, form: DetailedContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        detailed_case_history: DetailedCaseHistory = form.save(commit=False)
        record_detailed_model_update_event(
            user=self.request.user,
            model_object=detailed_case_history,
            detailed_case=detailed_case_history.detailed_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to notes page"""
        return reverse(
            "detailed:create-case-note",
            kwargs={"case_id": self.object.detailed_case.id},
        )


class ManageContactDetailsUpdateView(DetailedCaseUpdateView):
    """View to list detailed case contacts"""

    form_class: type[DetailedManageContactsUpdateForm] = (
        DetailedManageContactsUpdateForm
    )
    template_name: str = "detailed/forms/manage_contacts.html"


class ContactCreateView(AddDetailedCaseToContextMixin, CreateView):
    """View to create detailed case contact"""

    model: type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: type[DetailedContactCreateForm] = DetailedContactCreateForm
    template_name: str = "detailed/forms/contact_create.html"

    def form_valid(self, form: DetailedContactCreateForm):
        """Populate detailed case of contact"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        contact: Contact = form.save(commit=False)
        contact.detailed_case = detailed_case
        contact.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        record_detailed_model_create_event(
            user=self.request.user,
            model_object=self.object,
            detailed_case=self.object.detailed_case,
        )
        return reverse(
            "detailed:manage-contact-details",
            kwargs={"pk": self.object.detailed_case.id},
        )


class ContactUpdateView(UpdateView):
    """View to update detailed case contact"""

    model: type[Contact] = Contact
    context_object_name: str = "contact"
    form_class: type[DetailedContactUpdateForm] = DetailedContactUpdateForm
    template_name: str = "detailed/forms/contact_update.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add detailed case into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["detailed_case"] = self.object.detailed_case
        return context

    def form_valid(self, form: DetailedContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        contact: Contact = form.save(commit=False)
        if "delete_contact" in self.request.POST:
            contact.is_deleted = True
        record_detailed_model_update_event(
            user=self.request.user,
            model_object=contact,
            detailed_case=contact.detailed_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        return reverse(
            "detailed:manage-contact-details",
            kwargs={"pk": self.object.detailed_case.id},
        )


class CorrespondenceUpdateView(DetailedCaseUpdateView):
    """View to update correspondence"""

    template_name: str = "detailed/forms/correspondence.html"


class ContactInformationRequestUpdateView(CorrespondenceUpdateView):
    """View to update request information for contact"""

    form_class: type[DetailedContactInformationRequestUpdateForm] = (
        DetailedContactInformationRequestUpdateForm
    )


class InitialTestingDetailsUpdateView(DetailedCaseUpdateView):
    """View to update initial testing details"""

    form_class: type[DetailedInitialTestingDetailsUpdateForm] = (
        DetailedInitialTestingDetailsUpdateForm
    )


class InitialTestingOutcomeUpdateView(DetailedCaseUpdateView):
    """View to update initial testing outcome"""

    form_class: type[DetailedInitialTestingOutcomeUpdateForm] = (
        DetailedInitialTestingOutcomeUpdateForm
    )


class ReportReadyForQAUpdateView(DetailedCaseUpdateView):
    """View to update report draft"""

    form_class: type[DetailedReportReadyForQAUpdateForm] = (
        DetailedReportReadyForQAUpdateForm
    )


class QAAuditorUpdateView(DetailedCaseUpdateView):
    """View to update QA auditor"""

    form_class: type[DetailedQAAuditorUpdateForm] = DetailedQAAuditorUpdateForm


class QACommentsUpdateView(DetailedCaseUpdateView):
    """View to add or update QA comments"""

    form_class: type[DetailedQACommentsUpdateForm] = DetailedQACommentsUpdateForm
    template_name: str = "detailed/forms/qa_comments.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        detailed_case: DetailedCase = self.object
        body: str = form.cleaned_data.get("body")
        if body:
            comment: Comment = Comment.objects.create(
                base_case=detailed_case,
                user=self.request.user,
                body=form.cleaned_data.get("body"),
            )
            record_detailed_model_create_event(
                user=self.request.user,
                model_object=comment,
                detailed_case=detailed_case,
            )
            add_comment_notification(self.request, comment)
        return HttpResponseRedirect(self.get_success_url())


class QAApprovalUpdateView(DetailedCaseUpdateView):
    """View to update report QA approval"""

    form_class: type[DetailedQAApprovalUpdateForm] = DetailedQAApprovalUpdateForm


class FinalReportUpdateView(DetailedCaseUpdateView):
    """View to update publish report"""

    form_class: type[DetailedFinalReportUpdateForm] = DetailedFinalReportUpdateForm


class CorrespondenceReportSentUpdateView(CorrespondenceUpdateView):
    """View to update correspondence report sent"""

    form_class: type[DetailedReportSentUpdateForm] = DetailedReportSentUpdateForm

    def form_valid(self, form: DetailedReportSentUpdateForm):
        """
        Populate 12-week deadline if report sent date has changed
        """
        self.object: DetailedCase = form.save(commit=False)
        if (
            "report_sent_date" in form.changed_data
            and form.cleaned_data["report_sent_date"]
            and self.object.twelve_week_deadline_date is None
        ):
            self.object.twelve_week_deadline_date = add_12_weeks_to_date(
                anchor_date=form.cleaned_data["report_sent_date"]
            )
        return super().form_valid(form)


class CorrespondenceReportAcknowledgedUpdateView(CorrespondenceUpdateView):
    """View to update correspondence report acknowledged"""

    form_class: type[DetailedReportAcknowledgedUpdateForm] = (
        DetailedReportAcknowledgedUpdateForm
    )


class CorrespondenceTwelveWeekDeadlineUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week deadline"""

    form_class: type[DetailedTwelveWeekDeadlineUpdateForm] = (
        DetailedTwelveWeekDeadlineUpdateForm
    )


class CorrespondenceTwelveWeekRequestUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week update request"""

    form_class: type[DetailedTwelveWeekRequestUpdateForm] = (
        DetailedTwelveWeekRequestUpdateForm
    )


class CorrespondenceTwelveWeekReceivedUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week update received"""

    form_class: type[DetailedTwelveWeekReceivedUpdateForm] = (
        DetailedTwelveWeekReceivedUpdateForm
    )


class RetestResultUpdateView(DetailedCaseUpdateView):
    """View to update reviewing changes retesting"""

    form_class: type[DetailedRetestResultUpdateForm] = DetailedRetestResultUpdateForm
    template_name: str = "detailed/forms/retesting.html"


class RetestComplianceDecisionsUpdateView(DetailedCaseUpdateView):
    """View to update reviewing changes retest result"""

    form_class: type[DetailedRetestComplianceDecisionsUpdateForm] = (
        DetailedRetestComplianceDecisionsUpdateForm
    )
    template_name: str = "detailed/forms/retesting.html"


class CaseRecommendationUpdateView(DetailedCaseUpdateView):
    """View to update case recommendation"""

    form_class: type[DetailedCaseRecommendationUpdateForm] = (
        DetailedCaseRecommendationUpdateForm
    )
    template_name: str = "detailed/forms/recommendation.html"


class CaseCloseUpdateView(DetailedCaseUpdateView):
    """View to update closing the case"""

    form_class: type[DetailedCaseCloseUpdateForm] = DetailedCaseCloseUpdateForm
    template_name: str = "cases/closing_case.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        detailed_case: DetailedCase = self.object
        equality_body_metadata_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=detailed_case,
                column_definitions=DETAILED_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_report_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=detailed_case,
                column_definitions=DETAILED_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_correspondence_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=detailed_case,
                column_definitions=DETAILED_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_test_summary_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=detailed_case,
                column_definitions=DETAILED_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
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


class StatementEnforcementUpdateView(DetailedCaseUpdateView):
    """View to update post case statement enforcement"""

    form_class: type[DetailedStatementEnforcementUpdateForm] = (
        DetailedStatementEnforcementUpdateForm
    )


class EnforcementBodyMetadataUpdateView(DetailedCaseUpdateView):
    """View to update post case equality body metadata"""

    form_class: type[DetailedEnforcementBodyMetadataUpdateForm] = (
        DetailedEnforcementBodyMetadataUpdateForm
    )


class CaseZendeskTicketsDetailView(HideCaseNavigationMixin, DetailView):
    """
    View of Zendesk tickets for a detailed case
    """

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "case"
    template_name: str = "detailed/zendesk_tickets.html"


class ZendeskTicketCreateView(HideCaseNavigationMixin, CreateView):
    """
    View to create a Zendesk ticket
    """

    model: type[DetailedCase] = ZendeskTicket
    form_class: type[DetailedZendeskTicketCreateUpdateForm] = (
        DetailedZendeskTicketCreateUpdateForm
    )
    template_name: str = "detailed/forms/zendesk_ticket_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context as object"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        context["object"] = detailed_case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        zendesk_ticket: ZendeskTicket = form.save(commit=False)
        zendesk_ticket.detailed_case = detailed_case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        zendesk_ticket: ZendeskTicket = self.object
        user: User = self.request.user
        record_detailed_model_create_event(
            user=user,
            model_object=zendesk_ticket,
            detailed_case=zendesk_ticket.detailed_case,
        )
        case_pk: dict[str, int] = {"pk": zendesk_ticket.detailed_case.id}
        return reverse("detailed:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketUpdateView(HideCaseNavigationMixin, UpdateView):
    """
    View to update Zendesk ticket
    """

    model: type[ZendeskTicket] = ZendeskTicket
    form_class: type[DetailedZendeskTicketCreateUpdateForm] = (
        DetailedZendeskTicketCreateUpdateForm
    )
    context_object_name: str = "zendesk_ticket"
    template_name: str = "detailed/forms/zendesk_ticket_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add update event"""
        if form.changed_data:
            zendesk_ticket: ZendeskTicket = form.save(commit=False)
            user: User = self.request.user
            record_detailed_model_update_event(
                user=user,
                model_object=zendesk_ticket,
                detailed_case=zendesk_ticket.detailed_case,
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to zendesk tickets page on save"""
        zendesk_ticket: ZendeskTicket = self.object
        case_pk: dict[str, int] = {"pk": zendesk_ticket.detailed_case.id}
        return reverse("detailed:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketConfirmDeleteUpdateView(ZendeskTicketUpdateView):
    """
    View to confirm delete of Zendesk ticket
    """

    form_class: type[DetailedZendeskTicketConfirmDeleteUpdateForm] = (
        DetailedZendeskTicketConfirmDeleteUpdateForm
    )
    template_name: str = "detailed/forms/zendesk_ticket_confirm_delete.html"


class UnresponsivePSBUpdateView(
    MessageOnSaveMixin, HideCaseNavigationMixin, DetailedCaseUpdateView
):
    """View to set unresponsive PSB flag"""

    form_class: type[DetailedUnresponsivePSBUpdateForm] = (
        DetailedUnresponsivePSBUpdateForm
    )
    template_name: str = "detailed/forms/unresponsive_psb.html"


class DetailedCaseHistoryDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "case"
    template_name: str = "cases/case_history.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add current case to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        detailed_case: DetailedCase = self.object
        event_history: DetailedEventHistory = DetailedEventHistory.objects.filter(
            detailed_case=detailed_case
        ).prefetch_related("parent")
        context["event_history"] = event_history
        context["all_users"] = User.objects.all().order_by("id")
        return context


def mark_qa_comments_as_read(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark QA comment reminders as read for the current user"""
    detailed_case: DetailedCase = DetailedCase.objects.get(id=pk)
    mark_tasks_as_read(
        user=request.user, base_case=detailed_case, type=Task.Type.QA_COMMENT
    )
    mark_tasks_as_read(
        user=request.user, base_case=detailed_case, type=Task.Type.REPORT_APPROVED
    )
    messages.success(request, f"{detailed_case} comments marked as read")
    return redirect(
        reverse("detailed:edit-qa-comments", kwargs={"pk": detailed_case.id})
    )


def export_detailed_cases(request: HttpRequest) -> HttpResponse:
    """View to export detailed cases"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.DETAILED
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_detailed_cases(detailed_cases=filter_cases(form=case_search_form))


def export_feedback_survey_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for feedback survey"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.DETAILED
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form.is_valid()
    return download_detailed_feedback_survey_cases(
        cases=filter_cases(form=case_search_form)
    )


def export_equality_body_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for equality body survey"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.DETAILED
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form.is_valid()
    return download_detailed_equality_body_cases(
        cases=filter_cases(form=case_search_form)
    )


class CaseEmailTemplateListView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, ListView
):
    """View of list of email templates for the case"""

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "common/emails/template_list.html"
    context_object_name: str = "email_templates"

    def get_queryset(self) -> QuerySet[EmailTemplate]:
        """Add filters to queryset"""
        return EmailTemplate.objects.filter(is_deleted=False, is_detailed=True)


class CaseEmailTemplatePreviewDetailView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, DetailView
):
    """View email template populated with case data"""

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "common/emails/template_preview.html"
    context_object_name: str = "email_template"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case and email template to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        context["case"] = detailed_case
        context["email_template_name"] = (
            f"common/emails/templates/{self.object.template_name}.html"
        )
        extra_context = get_detailed_mobile_email_template_context()
        return {**extra_context, **context}
