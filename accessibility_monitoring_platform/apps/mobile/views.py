"""
Views for cases app
"""

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

from ..cases.csv_export import populate_equality_body_columns
from ..cases.forms import CaseSearchForm
from ..cases.models import BaseCase, TestType
from ..cases.utils import filter_cases, find_duplicate_cases
from ..comments.models import Comment
from ..comments.utils import add_comment_notification
from ..common.csv_export import EqualityBodyCSVColumn
from ..common.sitemap import Sitemap
from ..common.utils import extract_domain_from_url, replace_search_key_with_case_search
from ..common.views import (
    HideCaseNavigationMixin,
    NextPlatformPageMixin,
    ShowGoBackJSWidgetMixin,
)
from ..notifications.models import Task
from ..notifications.utils import mark_tasks_as_read
from .csv_export import (
    MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
    MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
)
from .forms import (
    CaseCloseUpdateForm,
    CaseRecommendationUpdateForm,
    ContactCreateForm,
    ContactInformationRequestUpdateForm,
    ContactUpdateForm,
    EnforcementBodyMetadataUpdateForm,
    FinalReportUpdateForm,
    InitialTestingDetailsUpdateForm,
    InitialTestingOutcomeUpdateForm,
    ManageContactsUpdateForm,
    MobileCaseCreateForm,
    MobileCaseHistoryCreateForm,
    MobileCaseHistoryUpdateForm,
    MobileCaseMetadataUpdateForm,
    MobileCaseStatusUpdateForm,
    QAApprovalUpdateForm,
    QAAuditorUpdateForm,
    QACommentsUpdateForm,
    ReportAcknowledgedUpdateForm,
    ReportReadyForQAUpdateForm,
    ReportSentUpdateForm,
    RetestComplianceDecisionsUpdateForm,
    RetestResultUpdateForm,
    StatementEnforcementUpdateForm,
    TwelveWeekDeadlineUpdateForm,
    TwelveWeekReceivedUpdateForm,
    TwelveWeekRequestUpdateForm,
    UnresponsivePSBUpdateForm,
    ZendeskTicketConfirmDeleteUpdateForm,
    ZendeskTicketCreateUpdateForm,
)
from .models import (
    EventHistory,
    MobileCase,
    MobileCaseHistory,
    MobileContact,
    MobileZendeskTicket,
)
from .utils import (
    add_to_mobile_case_history,
    download_mobile_cases,
    download_mobile_equality_body_cases,
    download_mobile_feedback_survey_cases,
    get_mobile_case_detail_sections,
    record_mobile_model_create_event,
    record_mobile_model_update_event,
)


class AddMobileCaseToContextMixin:
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add mobile case into context"""
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["mobile_case"] = mobile_case
        return context


class MessageOnSaveMixin:
    def get_success_url(self) -> str:
        messages.add_message(
            self.request,
            messages.INFO,
            "Page saved",
        )
        return super().get_success_url()


class MobileCaseCreateView(ShowGoBackJSWidgetMixin, CreateView):
    """
    View to create a case
    """

    model: type[MobileCase] = MobileCase
    form_class: type[MobileCaseCreateForm] = MobileCaseCreateForm
    context_object_name: str = "mobile_case"
    template_name: str = "mobile/forms/create.html"

    def form_valid(self, form: MobileCaseCreateForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            mobile_case: MobileCase = form.save(commit=False)
            mobile_case.created_by = self.request.user
            mobile_case.test_type = MobileCase.TestType.MOBILE
            return super().form_valid(form)

        context: dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[BaseCase] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            new_case: MobileCase = form.save(commit=False)
            new_case.test_type = MobileCase.TestType.MOBILE
            context["new_case"] = new_case
            return self.render_to_response(context)

        mobile_case: MobileCase = form.save(commit=False)
        mobile_case.created_by = self.request.user
        mobile_case.test_type = MobileCase.TestType.MOBILE
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        mobile_case: MobileCase = self.object
        user: User = self.request.user
        record_mobile_model_create_event(
            user=user, model_object=mobile_case, mobile_case=mobile_case
        )
        case_pk: dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("mobile:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("mobile:case-create")
        else:
            url: str = reverse("cases:case-list")
        return url


class MobileCaseDetailView(DetailView):
    """View of details of a single mobile Case"""

    model: type[MobileCase] = MobileCase
    context_object_name: str = "mobile_case"


class CaseDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[MobileCase] = MobileCase
    context_object_name: str = "mobile_case"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case detail sections to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        mobile_case: MobileCase = self.object
        sitemap: Sitemap = Sitemap(request=self.request)

        return {
            **{
                "case_detail_sections": get_mobile_case_detail_sections(
                    mobile_case=mobile_case, sitemap=sitemap
                )
            },
            **context,
        }


class CaseSearchView(HideCaseNavigationMixin, CaseDetailView):
    """
    View and search details of a single case
    """

    template_name: str = "mobile/case_search_all_data.html"


class MobileCaseUpdateView(NextPlatformPageMixin, UpdateView):
    """View to update MobileCase"""

    model: type[MobileCase] = MobileCase
    context_object_name: str = "mobile_case"
    template_name: str = "mobile/base.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of mobile case"""
        if form.changed_data:
            self.object: MobileCase = form.save(commit=False)
            user: User = self.request.user
            record_mobile_model_update_event(
                user=user, model_object=self.object, mobile_case=self.object
            )
            self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class MobileCaseMetadataUpdateView(MobileCaseUpdateView):
    """View to update mobile case metadata"""

    form_class: type[MobileCaseMetadataUpdateForm] = MobileCaseMetadataUpdateForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: MobileCase = form.save(commit=False)
            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)
        return super().form_valid(form)


class MobileCaseStatusUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to update mobile case status"""

    model: type[MobileCase] = MobileCase
    form_class: type[MobileCaseStatusUpdateForm] = MobileCaseStatusUpdateForm
    context_object_name: str = "mobile_case"
    template_name: str = "mobile/forms/case_status.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: MobileCase = form.save(commit=False)
            user: User = self.request.user
            record_mobile_model_update_event(
                user=user, model_object=self.object, mobile_case=self.object
            )
            self.object.save()
            add_to_mobile_case_history(
                mobile_case=self.object,
                user=user,
                value=self.object.get_status_display(),
                event_type=MobileCaseHistory.EventType.STATUS,
            )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Stay on page"""
        return self.request.path


class MobileCaseNoteCreateView(HideCaseNavigationMixin, CreateView):
    """View to add a note to the MobileCaseHistory"""

    model: type[MobileCaseHistory] = MobileCaseHistory
    form_class: type[MobileCaseHistoryCreateForm] = MobileCaseHistoryCreateForm
    context_object_name: str = "mobile_case_history"
    template_name: str = "mobile/forms/note_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["mobile_case"] = mobile_case
        context["mobile_case_history"] = mobile_case.mobilecasehistory_set.all()
        return context

    def form_valid(self, form: MobileCaseHistoryCreateForm):
        """Process contents of valid form"""
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        mobile_case_history: MobileCaseHistory = form.save(commit=False)
        mobile_case_history.mobile_case = mobile_case
        mobile_case_history.created_by = self.request.user
        mobile_case_history.label = mobile_case.get_status_display()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        mobile_case_history: MobileCaseHistory = self.object
        mobile_case: MobileCase = mobile_case_history.mobile_case
        user: User = self.request.user
        record_mobile_model_create_event(
            user=user,
            model_object=mobile_case_history,
            mobile_case=mobile_case,
        )
        return reverse("mobile:create-case-note", kwargs={"case_id": mobile_case.id})


class MobileCaseNoteUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to edit a note on the MobileCaseHistory"""

    model: type[MobileCaseHistory] = MobileCaseHistory
    form_class: type[MobileCaseHistoryUpdateForm] = MobileCaseHistoryUpdateForm
    context_object_name: str = "mobile_case_history"
    template_name: str = "mobile/forms/note_update.html"

    def form_valid(self, form: ContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        mobile_case_history: MobileCaseHistory = form.save(commit=False)
        record_mobile_model_update_event(
            user=self.request.user,
            model_object=mobile_case_history,
            mobile_case=mobile_case_history.mobile_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to notes page"""
        return reverse(
            "mobile:create-case-note",
            kwargs={"case_id": self.object.mobile_case.id},
        )


class ManageContactDetailsUpdateView(MobileCaseUpdateView):
    """View to list mobile case contacts"""

    form_class: type[ManageContactsUpdateForm] = ManageContactsUpdateForm
    template_name: str = "mobile/forms/manage_contacts.html"


class ContactCreateView(AddMobileCaseToContextMixin, CreateView):
    """View to create mobile case contact"""

    model: type[MobileContact] = MobileContact
    context_object_name: str = "contact"
    form_class: type[ContactCreateForm] = ContactCreateForm
    template_name: str = "mobile/forms/contact_create.html"

    def form_valid(self, form: ContactCreateForm):
        """Populate mobile case of contact"""
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        contact: MobileContact = form.save(commit=False)
        contact.mobile_case = mobile_case
        contact.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        record_mobile_model_create_event(
            user=self.request.user,
            model_object=self.object,
            mobile_case=self.object.mobile_case,
        )
        return reverse(
            "mobile:manage-contact-details",
            kwargs={"pk": self.object.mobile_case.id},
        )


class ContactUpdateView(UpdateView):
    """View to update mobile case contact"""

    model: type[MobileContact] = MobileContact
    context_object_name: str = "contact"
    form_class: type[ContactUpdateForm] = ContactUpdateForm
    template_name: str = "mobile/forms/contact_update.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add mobile case into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["mobile_case"] = self.object.mobile_case
        return context

    def form_valid(self, form: ContactUpdateForm):
        """Mark contact as deleted if button is pressed"""
        contact: MobileContact = form.save(commit=False)
        if "delete_contact" in self.request.POST:
            contact.is_deleted = True
        record_mobile_model_update_event(
            user=self.request.user,
            model_object=contact,
            mobile_case=contact.mobile_case,
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to the list of contact details"""
        return reverse(
            "mobile:manage-contact-details",
            kwargs={"pk": self.object.mobile_case.id},
        )


class CorrespondenceUpdateView(MobileCaseUpdateView):
    """View to update correspondence"""

    template_name: str = "mobile/forms/correspondence.html"


class ContactInformationRequestUpdateView(CorrespondenceUpdateView):
    """View to update request information for contact"""

    form_class: type[ContactInformationRequestUpdateForm] = (
        ContactInformationRequestUpdateForm
    )


class InitialTestingDetailsUpdateView(MobileCaseUpdateView):
    """View to update initial testing details"""

    form_class: type[InitialTestingDetailsUpdateForm] = InitialTestingDetailsUpdateForm


class InitialTestingOutcomeUpdateView(MobileCaseUpdateView):
    """View to update initial testing outcome"""

    form_class: type[InitialTestingOutcomeUpdateForm] = InitialTestingOutcomeUpdateForm


class ReportReadyForQAUpdateView(MobileCaseUpdateView):
    """View to update report draft"""

    form_class: type[ReportReadyForQAUpdateForm] = ReportReadyForQAUpdateForm


class QAAuditorUpdateView(MobileCaseUpdateView):
    """View to update QA auditor"""

    form_class: type[QAAuditorUpdateForm] = QAAuditorUpdateForm


class QACommentsUpdateView(MobileCaseUpdateView):
    """View to add or update QA comments"""

    form_class: type[QACommentsUpdateForm] = QACommentsUpdateForm
    template_name: str = "mobile/forms/qa_comments.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        mobile_case: MobileCase = self.object
        body: str = form.cleaned_data.get("body")
        if body:
            comment: Comment = Comment.objects.create(
                base_case=mobile_case,
                user=self.request.user,
                body=form.cleaned_data.get("body"),
            )
            record_mobile_model_create_event(
                user=self.request.user,
                model_object=comment,
                mobile_case=mobile_case,
            )
            add_comment_notification(self.request, comment)
        return HttpResponseRedirect(self.get_success_url())


class QAApprovalUpdateView(MobileCaseUpdateView):
    """View to update report QA approval"""

    form_class: type[QAApprovalUpdateForm] = QAApprovalUpdateForm


class FinalReportUpdateView(MobileCaseUpdateView):
    """View to update publish report"""

    form_class: type[FinalReportUpdateForm] = FinalReportUpdateForm


class CorrespondenceReportSentUpdateView(CorrespondenceUpdateView):
    """View to update correspondence report sent"""

    form_class: type[ReportSentUpdateForm] = ReportSentUpdateForm


class CorrespondenceReportAcknowledgedUpdateView(CorrespondenceUpdateView):
    """View to update correspondence report acknowledged"""

    form_class: type[ReportAcknowledgedUpdateForm] = ReportAcknowledgedUpdateForm


class CorrespondenceTwelveWeekDeadlineUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week deadline"""

    form_class: type[TwelveWeekDeadlineUpdateForm] = TwelveWeekDeadlineUpdateForm


class CorrespondenceTwelveWeekRequestUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week update request"""

    form_class: type[TwelveWeekRequestUpdateForm] = TwelveWeekRequestUpdateForm


class CorrespondenceTwelveWeekReceivedUpdateView(CorrespondenceUpdateView):
    """View to update correspondence 12-week received"""

    form_class: type[TwelveWeekReceivedUpdateForm] = TwelveWeekReceivedUpdateForm


class RetestResultUpdateView(MobileCaseUpdateView):
    """View to update reviewing changes retesting"""

    form_class: type[RetestResultUpdateForm] = RetestResultUpdateForm
    template_name: str = "mobile/forms/retesting.html"


class RetestComplianceDecisionsUpdateView(MobileCaseUpdateView):
    """View to update reviewing changes retest result"""

    form_class: type[RetestComplianceDecisionsUpdateForm] = (
        RetestComplianceDecisionsUpdateForm
    )


class CaseRecommendationUpdateView(MobileCaseUpdateView):
    """View to update case recommendation"""

    form_class: type[CaseRecommendationUpdateForm] = CaseRecommendationUpdateForm
    template_name: str = "mobile/forms/recommendation.html"


class CaseCloseUpdateView(MobileCaseUpdateView):
    """View to update closing the case"""

    form_class: type[CaseCloseUpdateForm] = CaseCloseUpdateForm
    template_name: str = "cases/closing_case.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        mobile_case: MobileCase = self.object
        equality_body_metadata_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=mobile_case,
                column_definitions=MOBILE_EQUALITY_BODY_METADATA_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_report_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=mobile_case,
                column_definitions=MOBILE_EQUALITY_BODY_REPORT_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_correspondence_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=mobile_case,
                column_definitions=MOBILE_EQUALITY_BODY_CORRESPONDENCE_COLUMNS_FOR_EXPORT,
            )
        )
        equality_body_test_summary_columns: list[EqualityBodyCSVColumn] = (
            populate_equality_body_columns(
                case=mobile_case,
                column_definitions=MOBILE_EQUALITY_BODY_TEST_SUMMARY_COLUMNS_FOR_EXPORT,
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


class StatementEnforcementUpdateView(MobileCaseUpdateView):
    """View to update post case statement enforcement"""

    form_class: type[StatementEnforcementUpdateForm] = StatementEnforcementUpdateForm


class EnforcementBodyMetadataUpdateView(MobileCaseUpdateView):
    """View to update post case equality body metadata"""

    form_class: type[EnforcementBodyMetadataUpdateForm] = (
        EnforcementBodyMetadataUpdateForm
    )


class CaseZendeskTicketsDetailView(
    HideCaseNavigationMixin, ShowGoBackJSWidgetMixin, DetailView
):
    """
    View of Zendesk tickets for a mobile case
    """

    model: type[MobileCase] = MobileCase
    context_object_name: str = "case"
    template_name: str = "mobile/zendesk_tickets.html"


class ZendeskTicketCreateView(HideCaseNavigationMixin, CreateView):
    """
    View to create a Zendesk ticket
    """

    model: type[MobileZendeskTicket] = MobileZendeskTicket
    form_class: type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    template_name: str = "mobile/forms/zendesk_ticket_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context as object"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        context["object"] = mobile_case
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        mobile_case: MobileCase = get_object_or_404(
            MobileCase, id=self.kwargs.get("case_id")
        )
        zendesk_ticket: MobileZendeskTicket = form.save(commit=False)
        zendesk_ticket.mobile_case = mobile_case
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        zendesk_ticket: MobileZendeskTicket = self.object
        user: User = self.request.user
        record_mobile_model_create_event(
            user=user,
            model_object=zendesk_ticket,
            mobile_case=zendesk_ticket.mobile_case,
        )
        case_pk: dict[str, int] = {"pk": zendesk_ticket.mobile_case.id}
        return reverse("mobile:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketUpdateView(HideCaseNavigationMixin, UpdateView):
    """
    View to update Zendesk ticket
    """

    model: type[MobileZendeskTicket] = MobileZendeskTicket
    form_class: type[ZendeskTicketCreateUpdateForm] = ZendeskTicketCreateUpdateForm
    context_object_name: str = "zendesk_ticket"
    template_name: str = "mobile/forms/zendesk_ticket_update.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add update event"""
        if form.changed_data:
            zendesk_ticket: MobileZendeskTicket = form.save(commit=False)
            user: User = self.request.user
            record_mobile_model_update_event(
                user=user,
                model_object=zendesk_ticket,
                mobile_case=zendesk_ticket.mobile_case,
            )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to zendesk tickets page on save"""
        zendesk_ticket: MobileZendeskTicket = self.object
        case_pk: dict[str, int] = {"pk": zendesk_ticket.mobile_case.id}
        return reverse("mobile:zendesk-tickets", kwargs=case_pk)


class ZendeskTicketConfirmDeleteUpdateView(ZendeskTicketUpdateView):
    """
    View to confirm delete of Zendesk ticket
    """

    form_class: type[ZendeskTicketConfirmDeleteUpdateForm] = (
        ZendeskTicketConfirmDeleteUpdateForm
    )
    template_name: str = "mobile/forms/zendesk_ticket_confirm_delete.html"


class UnresponsivePSBUpdateView(
    MessageOnSaveMixin, HideCaseNavigationMixin, MobileCaseUpdateView
):
    """View to set unresponsive PSB flag"""

    form_class: type[UnresponsivePSBUpdateForm] = UnresponsivePSBUpdateForm
    template_name: str = "mobile/forms/unresponsive_psb.html"


class MobileCaseHistoryDetailView(DetailView):
    """
    View of details of a single case
    """

    model: type[MobileCase] = MobileCase
    context_object_name: str = "case"
    template_name: str = "cases/case_history.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add current case to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        mobile_case: MobileCase = self.object
        event_history: EventHistory = EventHistory.objects.filter(
            mobile_case=mobile_case
        ).prefetch_related("parent")
        context["event_history"] = event_history
        context["all_users"] = User.objects.all().order_by("id")
        return context


def mark_qa_comments_as_read(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    """Mark QA comment reminders as read for the current user"""
    mobile_case: MobileCase = MobileCase.objects.get(id=pk)
    mark_tasks_as_read(
        user=request.user, base_case=mobile_case, type=Task.Type.QA_COMMENT
    )
    mark_tasks_as_read(
        user=request.user, base_case=mobile_case, type=Task.Type.REPORT_APPROVED
    )
    messages.success(request, f"{mobile_case} comments marked as read")
    return redirect(reverse("mobile:edit-qa-comments", kwargs={"pk": mobile_case.id}))


def export_mobile_cases(request: HttpRequest) -> HttpResponse:
    """View to export mobile cases"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.MOBILE
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form: CaseSearchForm = CaseSearchForm(
        replace_search_key_with_case_search(request.GET)
    )
    case_search_form.is_valid()
    return download_mobile_cases(mobile_cases=filter_cases(form=case_search_form))


def export_feedback_survey_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for feedback survey"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.MOBILE
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form.is_valid()
    return download_mobile_feedback_survey_cases(
        cases=filter_cases(form=case_search_form)
    )


def export_equality_body_cases(request: HttpRequest) -> HttpResponse:
    """View to export cases for equality body survey"""
    search_parameters: dict[str, str] = replace_search_key_with_case_search(request.GET)
    search_parameters["test_type"] = TestType.MOBILE
    case_search_form: CaseSearchForm = CaseSearchForm(search_parameters)
    case_search_form.is_valid()
    return download_mobile_equality_body_cases(
        cases=filter_cases(form=case_search_form)
    )
