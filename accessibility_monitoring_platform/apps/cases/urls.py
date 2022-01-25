"""
URLS for dashboard
"""
from typing import List

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls.resolvers import URLPattern
from accessibility_monitoring_platform.apps.cases.views import (
    export_cases,
    export_single_case,
    export_ehrc_cases,
    CaseCreateView,
    CaseContactFormsetUpdateView,
    CaseDetailView,
    CaseListView,
    CaseDetailUpdateView,
    CaseTestResultsUpdateView,
    CaseReportDetailsUpdateView,
    CaseQAProcessUpdateView,
    CaseReportCorrespondenceUpdateView,
    CaseReportFollowupDueDatesUpdateView,
    CaseDeleteUpdateView,
    CaseNoPSBResponseUpdateView,
    CaseTwelveWeekCorrespondenceUpdateView,
    CaseTwelveWeekCorrespondenceDueDatesUpdateView,
    CaseFinalDecisionUpdateView,
    CaseEnforcementBodyCorrespondenceUpdateView,
    CaseSuspendUpdateView,
    CaseUnsuspendUpdateView,
    restore_case,
)

app_name: str = "cases"
urlpatterns: List[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
    path(
        "export-as-ehrc-csv/",
        login_required(export_ehrc_cases),
        name="export-ehrc-cases",
    ),
    path("export-as-csv/", login_required(export_cases), name="case-export-list"),
    path(
        "<int:pk>/export-as-csv/",
        login_required(export_single_case),
        name="case-export-single",
    ),
    path("create/", login_required(CaseCreateView.as_view()), name="case-create"),
    path(
        "<int:pk>/view/", login_required(CaseDetailView.as_view()), name="case-detail"
    ),
    path(
        "<int:pk>/edit-case-details/",
        login_required(CaseDetailUpdateView.as_view()),
        name="edit-case-details",
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
        "<int:pk>/edit-qa-process/",
        login_required(CaseQAProcessUpdateView.as_view()),
        name="edit-qa-process",
    ),
    path(
        "<int:pk>/edit-contact-details/",
        login_required(CaseContactFormsetUpdateView.as_view()),
        name="edit-contact-details",
    ),
    path(
        "<int:pk>/edit-report-correspondence/",
        login_required(CaseReportCorrespondenceUpdateView.as_view()),
        name="edit-report-correspondence",
    ),
    path(
        "<int:pk>/edit-report-followup-due-dates/",
        login_required(CaseReportFollowupDueDatesUpdateView.as_view()),
        name="edit-report-followup-due-dates",
    ),
    path(
        "<int:pk>/edit-twelve-week-correspondence/",
        login_required(CaseTwelveWeekCorrespondenceUpdateView.as_view()),
        name="edit-twelve-week-correspondence",
    ),
    path(
        "<int:pk>/edit-twelve-week-correspondence-due-dates/",
        login_required(CaseTwelveWeekCorrespondenceDueDatesUpdateView.as_view()),
        name="edit-twelve-week-correspondence-due-dates",
    ),
    path(
        "<int:pk>/edit-no-psb-response/",
        login_required(CaseNoPSBResponseUpdateView.as_view()),
        name="edit-no-psb-response",
    ),
    path(
        "<int:pk>/edit-final-decision/",
        login_required(CaseFinalDecisionUpdateView.as_view()),
        name="edit-final-decision",
    ),
    path(
        "<int:pk>/edit-enforcement-body-correspondence/",
        login_required(CaseEnforcementBodyCorrespondenceUpdateView.as_view()),
        name="edit-enforcement-body-correspondence",
    ),
    path(
        "<int:pk>/delete-case/",
        login_required(CaseDeleteUpdateView.as_view()),
        name="delete-case",
    ),
    path(
        "<int:pk>/suspend-case/",
        login_required(CaseSuspendUpdateView.as_view()),
        name="suspend-case",
    ),
    path(
        "<int:pk>/unsuspend-case/",
        login_required(CaseUnsuspendUpdateView.as_view()),
        name="unsuspend-case",
    ),
    path(
        "<int:pk>/restore-case/",
        login_required(restore_case),
        name="restore-case",
    ),
]
