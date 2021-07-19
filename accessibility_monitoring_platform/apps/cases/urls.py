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
    CaseCreateView,
    CaseContactFormsetUpdateView,
    CaseDetailView,
    CaseListView,
    CaseDetailUpdateView,
    CaseTestResultsUpdateView,
    CaseReportDetailsUpdateView,
    CaseReportCorrespondanceUpdateView,
    CaseReportFollowupDueDatesUpdateView,
    CaseArchiveUpdateView,
    CaseNoPSBContactUpdateView,
    CaseNoPSBResponseUpdateView,
    CaseTwelveWeekCorrespondanceUpdateView,
    CaseTwelveWeekCorrespondanceDueDatesUpdateView,
    CaseFinalDecisionUpdateView,
    CaseEnforcementBodyCorrespondanceUpdateView,
)

app_name: str = "cases"
urlpatterns: List[URLPattern] = [
    path("", login_required(CaseListView.as_view()), name="case-list"),
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
        "<int:pk>/edit-contact-details/",
        login_required(CaseContactFormsetUpdateView.as_view()),
        name="edit-contact-details",
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
        "<int:pk>/edit-no-psb-contact/",
        login_required(CaseNoPSBContactUpdateView.as_view()),
        name="edit-no-psb-contact",
    ),
    path(
        "<int:pk>/edit-no-psb-response/",
        login_required(CaseNoPSBResponseUpdateView.as_view()),
        name="edit-no-psb-response",
    ),
    path(
        "<int:pk>/edit-report-correspondance/",
        login_required(CaseReportCorrespondanceUpdateView.as_view()),
        name="edit-report-correspondance",
    ),
    path(
        "<int:pk>/edit-report-followup-due-dates/",
        login_required(CaseReportFollowupDueDatesUpdateView.as_view()),
        name="edit-report-followup-due-dates",
    ),
    path(
        "<int:pk>/edit-12-week-correspondance/",
        login_required(CaseTwelveWeekCorrespondanceUpdateView.as_view()),
        name="edit-12-week-correspondance",
    ),
    path(
        "<int:pk>/edit-12-week-correspondance-due-dates/",
        login_required(CaseTwelveWeekCorrespondanceDueDatesUpdateView.as_view()),
        name="edit-12-week-correspondance-due-dates",
    ),
    path(
        "<int:pk>/edit-final-decision/",
        login_required(CaseFinalDecisionUpdateView.as_view()),
        name="edit-final-decision",
    ),
    path(
        "<int:pk>/edit-enforcement-body-correspondance/",
        login_required(CaseEnforcementBodyCorrespondanceUpdateView.as_view()),
        name="edit-enforcement-body-correspondance",
    ),
    path(
        "<int:pk>/archive-case/",
        login_required(CaseArchiveUpdateView.as_view()),
        name="archive-case",
    ),
]
