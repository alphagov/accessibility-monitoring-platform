"""
URLS for cases
"""

from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from accessibility_monitoring_platform.apps.cases.views import (
    CaseCloseUpdateView,
    CaseContactDetailsListUpdateView,
    CaseCreateView,
    CaseDeactivateUpdateView,
    CaseDetailView,
    CaseEmailTemplateListView,
    CaseEmailTemplatePreviewDetailView,
    CaseEnforcementRecommendationUpdateView,
    CaseEqualityBodyCorrespondenceUpdateView,
    CaseEqualityBodyMetadataUpdateView,
    CaseFourWeekContactDetailsUpdateView,
    CaseFourWeekFollowupUpdateView,
    CaseLegacyEndOfCaseUpdateView,
    CaseListView,
    CaseMetadataUpdateView,
    CaseNoPSBResponseUpdateView,
    CaseOneWeekContactDetailsUpdateView,
    CaseOneWeekFollowupFinalUpdateView,
    CaseOneWeekFollowupUpdateView,
    CaseOutstandingIssuesDetailView,
    CasePublishReportUpdateView,
    CaseQACommentsUpdateView,
    CaseReactivateUpdateView,
    CaseReportAcknowledgedUpdateView,
    CaseReportApprovedUpdateView,
    CaseReportDetailsUpdateView,
    CaseReportSentOnUpdateView,
    CaseRequestContactDetailsUpdateView,
    CaseRetestCreateErrorTemplateView,
    CaseRetestOverviewTemplateView,
    CaseReviewChangesUpdateView,
    CaseStatementEnforcementUpdateView,
    CaseStatusWorkflowDetailView,
    CaseTestResultsUpdateView,
    CaseTwelveWeekRetestUpdateView,
    CaseTwelveWeekUpdateAcknowledgedUpdateView,
    CaseTwelveWeekUpdateRequestedUpdateView,
    CaseZendeskTicketsDetailView,
    ContactCreateView,
    ContactUpdateView,
    EqualityBodyCorrespondenceCreateView,
    ListCaseEqualityBodyCorrespondenceUpdateView,
    PostCaseUpdateView,
    ZendeskTicketCreateView,
    ZendeskTicketUpdateView,
    delete_zendesk_ticket,
    export_cases,
    export_feedback_suvey_cases,
)

app_name: str = "cases"
urlpatterns: List[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path(
        "export-feedback-survey-cases-csv/",
        login_required(export_feedback_suvey_cases),
        name="export-feedback-survey-cases",
    ),
    path("export-as-csv/", login_required(export_cases), name="case-export-list"),
    path("create/", login_required(CaseCreateView.as_view()), name="case-create"),
    path(
        "<int:pk>/view/", login_required(CaseDetailView.as_view()), name="case-detail"
    ),
    path(
        "<int:pk>/edit-case-metadata/",
        login_required(CaseMetadataUpdateView.as_view()),
        name="edit-case-metadata",
    ),
    path(
        "<int:pk>/edit-test-results/",
        login_required(CaseTestResultsUpdateView.as_view()),
        name="edit-test-results",
    ),
    path(
        "<int:pk>/edit-report-details/",
        login_required(CaseReportDetailsUpdateView.as_view()),
        name="edit-report-details",
    ),
    path(
        "<int:pk>/edit-qa-comments/",
        login_required(CaseQACommentsUpdateView.as_view()),
        name="edit-qa-comments",
    ),
    path(
        "<int:pk>/edit-report-approved/",
        login_required(CaseReportApprovedUpdateView.as_view()),
        name="edit-report-approved",
    ),
    path(
        "<int:pk>/edit-publish-report/",
        login_required(CasePublishReportUpdateView.as_view()),
        name="edit-publish-report",
    ),
    path(
        "<int:pk>/edit-contact-details-list/",
        login_required(CaseContactDetailsListUpdateView.as_view()),
        name="edit-contact-details-list",
    ),
    path(
        "<int:case_id>/edit-contact-create/",
        login_required(ContactCreateView.as_view()),
        name="edit-contact-create",
    ),
    path(
        "contacts/<int:pk>/edit-contact-update/",
        login_required(ContactUpdateView.as_view()),
        name="edit-contact-update",
    ),
    path(
        "<int:pk>/edit-request-contact-details/",
        login_required(CaseRequestContactDetailsUpdateView.as_view()),
        name="edit-request-contact-details",
    ),
    path(
        "<int:pk>/edit-one-week-contact-details/",
        login_required(CaseOneWeekContactDetailsUpdateView.as_view()),
        name="edit-one-week-contact-details",
    ),
    path(
        "<int:pk>/edit-four-week-contact-details/",
        login_required(CaseFourWeekContactDetailsUpdateView.as_view()),
        name="edit-four-week-contact-details",
    ),
    path(
        "<int:pk>/edit-report-sent-on/",
        login_required(CaseReportSentOnUpdateView.as_view()),
        name="edit-report-sent-on",
    ),
    path(
        "<int:pk>/edit-one-week-followup/",
        login_required(CaseOneWeekFollowupUpdateView.as_view()),
        name="edit-one-week-followup",
    ),
    path(
        "<int:pk>/edit-four-week-followup/",
        login_required(CaseFourWeekFollowupUpdateView.as_view()),
        name="edit-four-week-followup",
    ),
    path(
        "<int:pk>/edit-report-acknowledged/",
        login_required(CaseReportAcknowledgedUpdateView.as_view()),
        name="edit-report-acknowledged",
    ),
    path(
        "<int:pk>/edit-12-week-update-requested/",
        login_required(CaseTwelveWeekUpdateRequestedUpdateView.as_view()),
        name="edit-12-week-update-requested",
    ),
    path(
        "<int:pk>/edit-one-week-followup-final/",
        login_required(CaseOneWeekFollowupFinalUpdateView.as_view()),
        name="edit-one-week-followup-final",
    ),
    path(
        "<int:pk>/edit-12-week-update-request-ack/",
        login_required(CaseTwelveWeekUpdateAcknowledgedUpdateView.as_view()),
        name="edit-12-week-update-request-ack",
    ),
    path(
        "<int:pk>/edit-no-psb-response/",
        login_required(CaseNoPSBResponseUpdateView.as_view()),
        name="edit-no-psb-response",
    ),
    path(
        "<int:pk>/edit-twelve-week-retest/",
        login_required(CaseTwelveWeekRetestUpdateView.as_view()),
        name="edit-twelve-week-retest",
    ),
    path(
        "<int:pk>/edit-review-changes/",
        login_required(CaseReviewChangesUpdateView.as_view()),
        name="edit-review-changes",
    ),
    path(
        "<int:pk>/edit-enforcement-recommendation/",
        login_required(CaseEnforcementRecommendationUpdateView.as_view()),
        name="edit-enforcement-recommendation",
    ),
    path(
        "<int:pk>/edit-case-close/",
        login_required(CaseCloseUpdateView.as_view()),
        name="edit-case-close",
    ),
    path(
        "<int:pk>/edit-post-case/",
        login_required(PostCaseUpdateView.as_view()),
        name="edit-post-case",
    ),
    path(
        "<int:pk>/deactivate-case/",
        login_required(CaseDeactivateUpdateView.as_view()),
        name="deactivate-case",
    ),
    path(
        "<int:pk>/reactivate-case/",
        login_required(CaseReactivateUpdateView.as_view()),
        name="reactivate-case",
    ),
    path(
        "<int:pk>/status-workflow/",
        login_required(CaseStatusWorkflowDetailView.as_view()),
        name="status-workflow",
    ),
    path(
        "<int:pk>/outstanding-issues/",
        login_required(CaseOutstandingIssuesDetailView.as_view()),
        name="outstanding-issues",
    ),
    path(
        "<int:pk>/statement-enforcement/",
        login_required(CaseStatementEnforcementUpdateView.as_view()),
        name="edit-statement-enforcement",
    ),
    path(
        "<int:pk>/equality-body-metadata/",
        login_required(CaseEqualityBodyMetadataUpdateView.as_view()),
        name="edit-equality-body-metadata",
    ),
    path(
        "<int:pk>/list-equality-body-correspondence/",
        login_required(ListCaseEqualityBodyCorrespondenceUpdateView.as_view()),
        name="list-equality-body-correspondence",
    ),
    path(
        "<int:case_id>/create-equality-body-correspondence/",
        login_required(EqualityBodyCorrespondenceCreateView.as_view()),
        name="create-equality-body-correspondence",
    ),
    path(
        "<int:pk>/edit-equality-body-correspondence/",
        login_required(CaseEqualityBodyCorrespondenceUpdateView.as_view()),
        name="edit-equality-body-correspondence",
    ),
    path(
        "<int:pk>/retest-overview/",
        login_required(CaseRetestOverviewTemplateView.as_view()),
        name="edit-retest-overview",
    ),
    path(
        "<int:pk>/retest-create-error/",
        login_required(CaseRetestCreateErrorTemplateView.as_view()),
        name="retest-create-error",
    ),
    path(
        "<int:pk>/legacy-end-of-case/",
        login_required(CaseLegacyEndOfCaseUpdateView.as_view()),
        name="legacy-end-of-case",
    ),
    path(
        "<int:pk>/zendesk-tickets/",
        login_required(CaseZendeskTicketsDetailView.as_view()),
        name="zendesk-tickets",
    ),
    path(
        "<int:case_id>/create-zendesk-ticket/",
        login_required(ZendeskTicketCreateView.as_view()),
        name="create-zendesk-ticket",
    ),
    path(
        "<int:pk>/update-zendesk-ticket/",
        login_required(ZendeskTicketUpdateView.as_view()),
        name="update-zendesk-ticket",
    ),
    path(
        "<int:pk>/delete-zendesk-ticket/",
        login_required(delete_zendesk_ticket),
        name="delete-zendesk-ticket",
    ),
    path(
        "<int:case_id>/email-template-list/",
        login_required(CaseEmailTemplateListView.as_view()),
        name="email-template-list",
    ),
    path(
        "<int:case_id>/<int:pk>/email-template-preview/",
        login_required(CaseEmailTemplatePreviewDetailView.as_view()),
        name="email-template-preview",
    ),
]
