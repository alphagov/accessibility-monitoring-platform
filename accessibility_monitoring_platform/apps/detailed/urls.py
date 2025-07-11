"""
URLS for cases
"""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern

from accessibility_monitoring_platform.apps.detailed.views import (
    CaseCloseUpdateView,
    ContactChasingRecordUpdateView,
    ContactCreateView,
    ContactInformationDeliveredUpdateView,
    ContactInformationRequestUpdateView,
    ContactUpdateView,
    CorrespondenceReportAcknowledgedUpdateView,
    CorrespondenceReportSentUpdateView,
    CorrespondenceTwelveWeekAcknowledgedUpdateView,
    CorrespondenceTwelveWeekDeadlineUpdateView,
    CorrespondenceTwelveWeekRequestUpdateView,
    DetailedCaseCreateView,
    DetailedCaseDetailView,
    DetailedCaseMetadataUpdateView,
    DetailedCaseNoteCreateView,
    DetailedCaseStatusUpdateView,
    EnforcementBodyMetadataUpdateView,
    InitialDisproportionateBurdenUpdateView,
    InitialStatementComplianceUpdateView,
    InitialTestingDetailsUpdateView,
    InitialTestingOutcomeUpdateView,
    InitialWebsiteComplianceUpdateView,
    ManageContactDetailsUpdateView,
    PublishReportUpdateView,
    QAApprovalUpdateView,
    ReportDraftUpdateView,
    RetestDisproportionateBurdenUpdateView,
    RetestMetricsUpdateView,
    RetestResultUpdateView,
    RetestStatementComplianceUpdateView,
    RetestSummaryUpdateView,
    RetestWebsiteComplianceUpdateView,
)

app_name: str = "detailed"
urlpatterns: list[URLPattern] = [
    path(
        "create/",
        login_required(DetailedCaseCreateView.as_view()),
        name="case-create",
    ),
    path(
        "<int:pk>/case-detail/",
        login_required(DetailedCaseDetailView.as_view()),
        name="case-detail",
    ),
    path(
        "<int:pk>/case-metadata/",
        login_required(DetailedCaseMetadataUpdateView.as_view()),
        name="edit-case-metadata",
    ),
    path(
        "<int:pk>/case-status/",
        login_required(DetailedCaseStatusUpdateView.as_view()),
        name="edit-case-status",
    ),
    path(
        "<int:case_id>/case-note-create/",
        login_required(DetailedCaseNoteCreateView.as_view()),
        name="create-case-note",
    ),
    path(
        "<int:pk>/manage-contact-details/",
        login_required(ManageContactDetailsUpdateView.as_view()),
        name="manage-contact-details",
    ),
    path(
        "<int:case_id>/edit-contact-create/",
        login_required(ContactCreateView.as_view()),
        name="edit-contact-create",
    ),
    path(
        "<int:pk>/edit-contact-update/",
        login_required(ContactUpdateView.as_view()),
        name="edit-contact-update",
    ),
    path(
        "<int:pk>/edit-request-contact-details/",
        login_required(ContactInformationRequestUpdateView.as_view()),
        name="edit-request-contact-details",
    ),
    path(
        "<int:pk>/edit-chasing-record/",
        login_required(ContactChasingRecordUpdateView.as_view()),
        name="edit-chasing-record",
    ),
    path(
        "<int:pk>/edit-information-delivered/",
        login_required(ContactInformationDeliveredUpdateView.as_view()),
        name="edit-information-delivered",
    ),
    path(
        "<int:pk>/edit-initial-testing-details/",
        login_required(InitialTestingDetailsUpdateView.as_view()),
        name="edit-initial-testing-details",
    ),
    path(
        "<int:pk>/edit-initial-testing-outcome/",
        login_required(InitialTestingOutcomeUpdateView.as_view()),
        name="edit-initial-testing-outcome",
    ),
    path(
        "<int:pk>/edit-initial-website-compliance/",
        login_required(InitialWebsiteComplianceUpdateView.as_view()),
        name="edit-initial-website-compliance",
    ),
    path(
        "<int:pk>/edit-disproportionate-burden-compliance/",
        login_required(InitialDisproportionateBurdenUpdateView.as_view()),
        name="edit-disproportionate-burden-compliance",
    ),
    path(
        "<int:pk>/edit-initial-statement-compliance/",
        login_required(InitialStatementComplianceUpdateView.as_view()),
        name="edit-initial-statement-compliance",
    ),
    path(
        "<int:pk>/edit-report-draft/",
        login_required(ReportDraftUpdateView.as_view()),
        name="edit-report-draft",
    ),
    path(
        "<int:pk>/edit-qa-approval/",
        login_required(QAApprovalUpdateView.as_view()),
        name="edit-qa-approval",
    ),
    path(
        "<int:pk>/edit-publish-report/",
        login_required(PublishReportUpdateView.as_view()),
        name="edit-publish-report",
    ),
    path(
        "<int:pk>/edit-report-sent/",
        login_required(CorrespondenceReportSentUpdateView.as_view()),
        name="edit-report-sent",
    ),
    path(
        "<int:pk>/edit-report-acknowledged/",
        login_required(CorrespondenceReportAcknowledgedUpdateView.as_view()),
        name="edit-report-acknowledged",
    ),
    path(
        "<int:pk>/edit-12-week-deadline/",
        login_required(CorrespondenceTwelveWeekDeadlineUpdateView.as_view()),
        name="edit-12-week-deadline",
    ),
    path(
        "<int:pk>/edit-12-week-request-update/",
        login_required(CorrespondenceTwelveWeekRequestUpdateView.as_view()),
        name="edit-12-week-request-update",
    ),
    path(
        "<int:pk>/edit-12-week-acknowledged/",
        login_required(CorrespondenceTwelveWeekAcknowledgedUpdateView.as_view()),
        name="edit-12-week-acknowledged",
    ),
    path(
        "<int:pk>/edit-retest-result/",
        login_required(RetestResultUpdateView.as_view()),
        name="edit-retest-result",
    ),
    path(
        "<int:pk>/edit-retest-summary/",
        login_required(RetestSummaryUpdateView.as_view()),
        name="edit-retest-summary",
    ),
    path(
        "<int:pk>/edit-retest-website-compliance/",
        login_required(RetestWebsiteComplianceUpdateView.as_view()),
        name="edit-retest-website-compliance",
    ),
    path(
        "<int:pk>/edit-retest-disproportionate-burden/",
        login_required(RetestDisproportionateBurdenUpdateView.as_view()),
        name="edit-retest-disproportionate-burden",
    ),
    path(
        "<int:pk>/edit-retest-statement-compliance/",
        login_required(RetestStatementComplianceUpdateView.as_view()),
        name="edit-retest-statement-compliance",
    ),
    path(
        "<int:pk>/edit-retest-metrics/",
        login_required(RetestMetricsUpdateView.as_view()),
        name="edit-retest-metrics",
    ),
    path(
        "<int:pk>/edit-case-close/",
        login_required(CaseCloseUpdateView.as_view()),
        name="edit-case-close",
    ),
    path(
        "<int:pk>/edit-equality-body-metadata/",
        login_required(EnforcementBodyMetadataUpdateView.as_view()),
        name="edit-equality-body-metadata",
    ),
]
