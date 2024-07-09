"""
Utility functions for cases app
"""

import copy
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django import forms
from django.contrib.auth.models import User
from django.db.models import Case as DjangoCase
from django.db.models import Q, QuerySet, When
from django.http.request import QueryDict
from django.urls import reverse

from ..audits.utils import (
    get_initial_test_view_sections,
    get_twelve_week_test_view_sections,
)
from ..common.form_extract_utils import (
    FieldLabelAndValue,
    extract_form_labels_and_values,
)
from ..common.templatetags.common_tags import amp_date, amp_datetime
from ..common.utils import build_filters
from ..common.view_section_utils import ViewSection, ViewSubTable, build_view_section
from .forms import (
    CaseCloseUpdateForm,
    CaseContactsUpdateForm,
    CaseDetailUpdateForm,
    CaseEnforcementRecommendationUpdateForm,
    CaseEqualityBodyMetadataUpdateForm,
    CaseFindContactDetailsUpdateForm,
    CaseFourWeekFollowupUpdateForm,
    CaseNoPSBContactUpdateForm,
    CaseOneWeekFollowupFinalUpdateForm,
    CaseOneWeekFollowupUpdateForm,
    CaseReportAcknowledgedUpdateForm,
    CaseReportApprovedUpdateForm,
    CaseReportDetailsUpdateForm,
    CaseReportSentOnUpdateForm,
    CaseReviewChangesUpdateForm,
    CaseStatementEnforcementUpdateForm,
    CaseTwelveWeekUpdateAcknowledgedUpdateForm,
    CaseTwelveWeekUpdateRequestedUpdateForm,
    PostCaseUpdateForm,
)
from .models import COMPLIANCE_FIELDS, Case, CaseEvent, CaseStatus, Complaint, Sort

CASE_FIELD_AND_FILTER_NAMES: List[Tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
]


@dataclass
class SubPage:
    name: str
    url: str
    complete: bool


@dataclass
class NavSection:
    name: str
    disabled: bool = False
    subpages: Optional[List[SubPage]] = None

    def number_complete(self) -> int:
        if self.subpages is not None:
            return len([subpage for subpage in self.subpages if subpage.complete])
        return 0


def build_case_sections(case: Case) -> List[NavSection]:
    """Return list of case sections for navigation details elements"""
    kwargs_case_pk: Dict[str, int] = {"pk": case.id}
    return [
        NavSection(
            name="Case details",
            subpages=[
                SubPage(
                    name="Case metadata",
                    url=reverse("cases:edit-case-details", kwargs=kwargs_case_pk),
                    complete=case.case_details_complete_date,
                )
            ],
        ),
    ]


def get_case_view_sections(case: Case) -> List[ViewSection]:
    """Get sections for case view"""
    get_case_rows: Callable = partial(extract_form_labels_and_values, instance=case)
    case_pk: Dict[str, int] = {"pk": case.id}
    case_details_prefix: List[FieldLabelAndValue] = [
        FieldLabelAndValue(
            label="Date created",
            value=case.created,
            type=FieldLabelAndValue.DATE_TYPE,
        ),
        FieldLabelAndValue(label="Status", value=case.status.get_status_display()),
    ]
    testing_details_subsections: Optional[List[ViewSection]] = None
    twelve_week_test_subsections: Optional[List[ViewSection]] = None
    report_details_fields: List[FieldLabelAndValue] = []
    equality_body_metadata: ViewSection = build_view_section(
        name="Equality body metadata",
        edit_url=reverse("cases:edit-equality-body-metadata", kwargs=case_pk),
        edit_url_id="edit-equality-body-metadata",
        display_fields=get_case_rows(form=CaseEqualityBodyMetadataUpdateForm()),
    )
    post_case_subsections: Optional[List[ViewSection]] = [
        build_view_section(
            name="Statement enforcement",
            edit_url=reverse("cases:edit-statement-enforcement", kwargs=case_pk),
            edit_url_id="edit-statement-enforcement",
            display_fields=get_case_rows(form=CaseStatementEnforcementUpdateForm()),
        ),
        equality_body_metadata,
        build_view_section(
            name="Equality body correspondence",
            edit_url=reverse("cases:list-equality-body-correspondence", kwargs=case_pk),
            edit_url_id="list-equality-body-correspondence",
            subtables=[
                ViewSubTable(
                    name=f"Zendesk correspondence #{equality_body_correspondence.id_within_case} ({equality_body_correspondence.get_status_display()})",
                    display_fields=[
                        FieldLabelAndValue(
                            label="Time added to platform",
                            value=amp_datetime(equality_body_correspondence.created),
                        ),
                        FieldLabelAndValue(
                            label="Type",
                            value=equality_body_correspondence.get_type_display(),
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.NOTES_TYPE,
                            label="Zendesk message",
                            value=equality_body_correspondence.message,
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.NOTES_TYPE,
                            label="Auditor notes",
                            value=equality_body_correspondence.notes,
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.URL_TYPE,
                            label="Link to Zendesk ticket",
                            value=equality_body_correspondence.zendesk_url,
                        ),
                    ],
                )
                for equality_body_correspondence in case.equalitybodycorrespondence_set.all()
            ],
        ),
        build_view_section(
            name="Equality body retest overview",
            edit_url=reverse("cases:edit-retest-overview", kwargs=case_pk),
            edit_url_id="edit-retest-overview",
            subtables=[
                ViewSubTable(
                    name=f"Retest #{equality_body_retest.id_within_case}",
                    display_fields=[
                        FieldLabelAndValue(
                            label="Date of retest",
                            value=amp_date(equality_body_retest.date_of_retest),
                        ),
                        FieldLabelAndValue(
                            label="Outcome",
                            value=equality_body_retest.get_retest_compliance_state_display(),
                        ),
                        FieldLabelAndValue(
                            label="Statement outcome",
                            value=equality_body_retest.get_statement_compliance_state_display(),
                        ),
                        FieldLabelAndValue(
                            label="WCAG issues",
                            value=f"{equality_body_retest.fixed_checks_count} of {equality_body_retest.case.audit.failed_check_results.count()} issues fixed",
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.NOTES_TYPE,
                            label="Retest notes",
                            value=equality_body_retest.retest_notes,
                        ),
                    ],
                )
                for equality_body_retest in case.retests.filter(id_within_case__gt=0)
            ],
        ),
    ]
    if case.archive:
        return post_case_subsections + [
            build_view_section(
                name="Legacy end of case data",
                edit_url=reverse("cases:legacy-end-of-case", kwargs=case_pk),
                edit_url_id="edit-post-case",
                display_fields=get_case_rows(form=PostCaseUpdateForm()),
            )
        ]
    if case.audit is not None:
        testing_details_subsections: List[FieldLabelAndValue] = (
            get_initial_test_view_sections(audit=case.audit)
        )
        twelve_week_test_subsections: List[FieldLabelAndValue] = (
            get_twelve_week_test_view_sections(audit=case.audit)
        )
        if case.report is not None:
            report_pk: Dict[str, int] = {"pk": case.report.id}
            report_details_fields: List[FieldLabelAndValue] = [
                FieldLabelAndValue(
                    type=FieldLabelAndValue.URL_TYPE,
                    external_url=False,
                    label="Preview report",
                    value=reverse("reports:report-publisher", kwargs=report_pk),
                    extra_label="Report publisher",
                ),
                FieldLabelAndValue(
                    type=FieldLabelAndValue.URL_TYPE,
                    label="View published HTML report",
                    value=case.published_report_url,
                    extra_label=case.report.latest_s3_report,
                ),
                FieldLabelAndValue(
                    type=FieldLabelAndValue.URL_TYPE,
                    external_url=False,
                    label="Report views",
                    value=reverse("reports:report-metrics-view", kwargs=report_pk),
                    extra_label=case.reportvisitsmetrics_set.all().count(),
                ),
                FieldLabelAndValue(
                    type=FieldLabelAndValue.URL_TYPE,
                    external_url=False,
                    label="Unique visitors to report",
                    value=f'{reverse("reports:report-metrics-view", kwargs=report_pk)}?showing=unique-visitors',
                    extra_label=case.reportvisitsmetrics_set.values_list(
                        "fingerprint_hash"
                    )
                    .distinct()
                    .count(),
                ),
            ]
    return [
        build_view_section(
            name="Case details",
            edit_url=reverse("cases:edit-case-details", kwargs=case_pk),
            edit_url_id="edit-case-details",
            complete_date=case.case_details_complete_date,
            display_fields=case_details_prefix
            + get_case_rows(form=CaseDetailUpdateForm()),
        ),
        build_view_section(
            name="Testing details",
            edit_url=reverse("cases:edit-test-results", kwargs=case_pk),
            edit_url_id="edit-test-results",
            complete_date=case.testing_details_complete_date,
            placeholder="A test does not exist for this case.",
            type=ViewSection.AUDIT_RESULTS_ON_VIEW_CASE,
            subsections=testing_details_subsections,
        ),
        build_view_section(
            name="Report details",
            edit_url=reverse("cases:edit-report-details", kwargs=case_pk),
            edit_url_id="edit-report-details",
            complete_date=case.reporting_details_complete_date,
            placeholder="A report does not exist for this case.",
            display_fields=(
                report_details_fields
                + get_case_rows(form=CaseReportDetailsUpdateForm())
                if case.report is not None
                else None
            ),
        ),
        build_view_section(
            name="QA comments",
            edit_url=reverse("cases:edit-qa-comments", kwargs=case_pk),
            edit_url_id="edit-qa-comments",
            display_fields=[
                FieldLabelAndValue(
                    type=FieldLabelAndValue.NOTES_TYPE,
                    label=f"{comment.user.get_full_name()} on {amp_datetime(comment.created_date)}",
                    value=comment.body,
                )
                for comment in case.qa_comments
            ],
        ),
        build_view_section(
            name="Report approved",
            edit_url=reverse("cases:edit-report-approved", kwargs=case_pk),
            edit_url_id="edit-report-approved",
            complete_date=case.qa_auditor_complete_date,
            display_fields=get_case_rows(form=CaseReportApprovedUpdateForm()),
        ),
        build_view_section(
            name="Publish report",
            edit_url=reverse("cases:edit-publish-report", kwargs=case_pk),
            edit_url_id="edit-publish-report",
            anchor="",
            complete_date=case.publish_report_complete_date,
        ),
        build_view_section(
            name="Find contact details",
            edit_url=reverse("cases:edit-find-contact-details", kwargs=case_pk),
            edit_url_id="edit-find-contact-details",
            complete_date=case.find_contact_details_complete_date,
            display_fields=get_case_rows(form=CaseFindContactDetailsUpdateForm()),
        ),
        build_view_section(
            name="Contact details",
            edit_url=reverse("cases:edit-contact-details", kwargs=case_pk),
            edit_url_id="edit-contact-details",
            complete_date=case.contact_details_complete_date,
            display_fields=get_case_rows(form=CaseContactsUpdateForm()),
            subtables=[
                ViewSubTable(
                    name=f"Contact {count}",
                    display_fields=[
                        FieldLabelAndValue(
                            label="Name",
                            value=contact.name,
                        ),
                        FieldLabelAndValue(
                            label="Job title",
                            value=contact.job_title,
                        ),
                        FieldLabelAndValue(
                            label="Email",
                            value=contact.email,
                        ),
                        FieldLabelAndValue(
                            label="Preferred contact",
                            value=contact.get_preferred_display(),
                        ),
                    ],
                )
                for count, contact in enumerate(case.contacts, start=1)
            ],
        ),
        build_view_section(
            name="Report sent on",
            edit_url=reverse("cases:edit-report-sent-on", kwargs=case_pk),
            edit_url_id="edit-report-sent-on",
            complete_date=case.report_sent_on_complete_date,
            display_fields=get_case_rows(form=CaseReportSentOnUpdateForm()),
        ),
        build_view_section(
            name="One week follow-up",
            edit_url=reverse("cases:edit-one-week-followup", kwargs=case_pk),
            edit_url_id="edit-one-week-followup",
            complete_date=case.one_week_followup_complete_date,
            display_fields=get_case_rows(form=CaseOneWeekFollowupUpdateForm()),
        ),
        build_view_section(
            name="Four week follow-up",
            edit_url=reverse("cases:edit-four-week-followup", kwargs=case_pk),
            edit_url_id="edit-four-week-followup",
            complete_date=case.four_week_followup_complete_date,
            display_fields=get_case_rows(form=CaseFourWeekFollowupUpdateForm()),
        ),
        build_view_section(
            name="Report acknowledged",
            edit_url=reverse("cases:edit-report-acknowledged", kwargs=case_pk),
            edit_url_id="edit-report-acknowledged",
            complete_date=case.report_acknowledged_complete_date,
            display_fields=get_case_rows(form=CaseReportAcknowledgedUpdateForm()),
        ),
        build_view_section(
            name="12-week update requested",
            edit_url=reverse("cases:edit-12-week-update-requested", kwargs=case_pk),
            edit_url_id="edit-12-week-update-requested",
            complete_date=case.twelve_week_update_requested_complete_date,
            display_fields=get_case_rows(
                form=CaseTwelveWeekUpdateRequestedUpdateForm()
            ),
        ),
        build_view_section(
            name="One week follow-up for final update",
            edit_url=reverse("cases:edit-one-week-followup-final", kwargs=case_pk),
            edit_url_id="edit-one-week-followup-final",
            complete_date=case.one_week_followup_final_complete_date,
            display_fields=get_case_rows(form=CaseOneWeekFollowupFinalUpdateForm()),
        ),
        build_view_section(
            name="12-week update request acknowledged",
            edit_url=reverse("cases:edit-12-week-update-request-ack", kwargs=case_pk),
            edit_url_id="edit-12-week-update-request-ack",
            complete_date=case.twelve_week_update_request_ack_complete_date,
            display_fields=get_case_rows(
                form=CaseTwelveWeekUpdateAcknowledgedUpdateForm()
            ),
        ),
        build_view_section(
            name="Public sector body is unresponsive",
            edit_url=reverse("cases:edit-no-psb-response", kwargs=case_pk),
            edit_url_id="edit-no-psb-response",
            display_fields=get_case_rows(form=CaseNoPSBContactUpdateForm()),
        ),
        build_view_section(
            name="PSB Zendesk tickets",
            edit_url=reverse("cases:zendesk-tickets", kwargs=case_pk),
            edit_url_id="zendesk-tickets",
            subtables=[
                ViewSubTable(
                    name=f"PSB Zendesk ticket {count}",
                    display_fields=[
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.URL_TYPE,
                            label="Zendesk link",
                            value=zendesk_ticket.url,
                        ),
                        FieldLabelAndValue(
                            type=FieldLabelAndValue.NOTES_TYPE,
                            label="Summary",
                            value=zendesk_ticket.summary,
                        ),
                    ],
                )
                for count, zendesk_ticket in enumerate(case.zendesk_tickets, start=1)
            ],
        ),
        build_view_section(
            name="Correspondence overview",
            edit_url=reverse("cases:edit-cores-overview", kwargs=case_pk),
            edit_url_id="edit-cores-overview",
            complete_date=case.cores_overview_complete_date,
            anchor="",
        ),
        build_view_section(
            name="12-week retest",
            edit_url=reverse("cases:edit-twelve-week-retest", kwargs=case_pk),
            edit_url_id="edit-twelve-week-retest",
            complete_date=case.twelve_week_retest_complete_date,
            type=ViewSection.AUDIT_RESULTS_ON_VIEW_CASE,
            subsections=twelve_week_test_subsections,
        ),
        build_view_section(
            name="Reviewing changes",
            edit_url=reverse("cases:edit-review-changes", kwargs=case_pk),
            edit_url_id="edit-review-changes",
            complete_date=case.review_changes_complete_date,
            display_fields=get_case_rows(form=CaseReviewChangesUpdateForm()),
        ),
        build_view_section(
            name="Enforcement recommendation",
            edit_url=reverse("cases:edit-enforcement-recommendation", kwargs=case_pk),
            edit_url_id="edit-enforcement-recommendation",
            complete_date=case.enforcement_recommendation_complete_date,
            display_fields=get_case_rows(
                form=CaseEnforcementRecommendationUpdateForm()
            ),
        ),
        build_view_section(
            name="Closing the case",
            edit_url=reverse("cases:edit-case-close", kwargs=case_pk),
            edit_url_id="edit-case-close",
            complete_date=case.case_close_complete_date,
            display_fields=get_case_rows(form=CaseCloseUpdateForm()),
        ),
    ] + post_case_subsections


def get_sent_date(
    form: forms.ModelForm, case_from_db: Case, sent_date_name: str
) -> Union[date, None]:
    """
    Work out what value to save in a sent date field on the case.
    If there is a new value in the form, don't replace an existing date on the database.
    If there is a new value in the form and no date on the database then use the date from the form.
    If there is no value in the form (i.e. the checkbox is unchecked), set the date on the database to None.
    """
    date_on_form: Optional[date] = form.cleaned_data.get(sent_date_name)
    if date_on_form is None:
        return None
    date_on_db: date = getattr(case_from_db, sent_date_name)
    return date_on_db if date_on_db else date_on_form


def filter_cases(form) -> QuerySet[Case]:  # noqa: C901
    """Return a queryset of Cases filtered by the values in CaseSearchForm"""
    filters: Dict = {}
    search_query = Q()
    sort_by: str = Sort.NEWEST

    if hasattr(form, "cleaned_data"):
        field_and_filter_names: List[Tuple[str, str]] = copy.copy(
            CASE_FIELD_AND_FILTER_NAMES
        )
        if "date_type" in form.cleaned_data:
            date_range_field: str = form.cleaned_data["date_type"]
            field_and_filter_names.append(("date_start", f"{date_range_field}__gte"))
            field_and_filter_names.append(("date_end", f"{date_range_field}__lte"))
        filters: Dict[str, Any] = build_filters(
            cleaned_data=form.cleaned_data,
            field_and_filter_names=field_and_filter_names,
        )
        sort_by: str = form.cleaned_data.get("sort_by", Sort.NEWEST)
        if form.cleaned_data.get("case_search"):
            search: str = form.cleaned_data["case_search"]
            if (
                search.isdigit()
            ):  # if its just a number, it presumes its an ID and returns that case
                search_query = Q(case_number=search)
            else:
                search_query = (
                    Q(  # pylint: disable=unsupported-binary-operation
                        organisation_name__icontains=search
                    )
                    | Q(home_page_url__icontains=search)
                    | Q(psb_location__icontains=search)
                    | Q(sector__name__icontains=search)
                    | Q(parental_organisation_name__icontains=search)
                    | Q(website_name__icontains=search)
                    | Q(subcategory__name__icontains=search)
                )
        for filter_name in ["is_complaint", "enforcement_body"]:
            filter_value: str = form.cleaned_data.get(filter_name, Complaint.ALL)
            if filter_value != Complaint.ALL:
                filters[filter_name] = filter_value

    if str(filters.get("status", "")) == CaseStatus.Status.READY_TO_QA:
        filters["qa_status"] = CaseStatus.Status.READY_TO_QA
        del filters["status"]

    if "status" in filters:
        filters["status__status"] = filters["status"]
        del filters["status"]

    # Auditor and reviewer may be filtered by unassigned
    if "auditor_id" in filters and filters["auditor_id"] == "none":
        filters["auditor_id"] = None
    if "reviewer_id" in filters and filters["reviewer_id"] == "none":
        filters["reviewer_id"] = None

    if not sort_by:
        return (
            Case.objects.filter(search_query, **filters)
            .annotate(
                position_unassigned_first=DjangoCase(
                    When(status__status=CaseStatus.Status.UNASSIGNED, then=0), default=1
                )
            )
            .order_by("position_unassigned_first", "-id")
            .select_related("auditor", "reviewer")
        )
    return (
        Case.objects.filter(search_query, **filters)
        .order_by(sort_by)
        .select_related("auditor", "reviewer")
    )


def replace_search_key_with_case_search(request_get: QueryDict) -> Dict[str, str]:
    """Convert QueryDict to dictionary and replace key 'search' with 'case_search'."""
    search_args: Dict[str, str] = {key: value for key, value in request_get.items()}
    if "search" in search_args:
        search_args["case_search"] = search_args.pop("search")
    return search_args


def record_case_event(
    user: User, new_case: Case, old_case: Optional[Case] = None
) -> None:
    """Create a case event based on the changes between the old and new cases"""
    if old_case is None:
        CaseEvent.objects.create(
            case=new_case, done_by=user, event_type=CaseEvent.EventType.CREATE
        )
        return
    if old_case.auditor != new_case.auditor:
        old_user_name: str = (
            old_case.auditor.get_full_name() if old_case.auditor is not None else "none"
        )
        new_user_name: str = (
            new_case.auditor.get_full_name() if new_case.auditor is not None else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.AUDITOR,
            message=f"Auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.audit is None and new_case.audit is not None:
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CREATE_AUDIT,
            message="Start of test",
        )
    if old_case.report_review_status != new_case.report_review_status:
        old_status: str = old_case.get_report_review_status_display()
        new_status: str = new_case.get_report_review_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_QA,
            message=f"Report ready to be reviewed changed from '{old_status}' to '{new_status}'",
        )
    if old_case.reviewer != new_case.reviewer:
        old_user_name: str = (
            old_case.reviewer.get_full_name()
            if old_case.reviewer is not None
            else "none"
        )
        new_user_name: str = (
            new_case.reviewer.get_full_name()
            if new_case.reviewer is not None
            else "none"
        )
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.QA_AUDITOR,
            message=f"QA auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.report_approved_status != new_case.report_approved_status:
        old_status: str = old_case.get_report_approved_status_display()
        new_status: str = new_case.get_report_approved_status_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.APPROVE_REPORT,
            message=f"Report approved changed from '{old_status}' to '{new_status}'",
        )
    if old_case.is_ready_for_final_decision != new_case.is_ready_for_final_decision:
        old_status: str = old_case.get_is_ready_for_final_decision_display()
        new_status: str = new_case.get_is_ready_for_final_decision_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_FINAL_DECISION,
            message=f"Case ready for final decision changed from '{old_status}' to '{new_status}'",
        )
    if old_case.case_completed != new_case.case_completed:
        old_status: str = old_case.get_case_completed_display()
        new_status: str = new_case.get_case_completed_display()
        CaseEvent.objects.create(
            case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CASE_COMPLETED,
            message=f"Case completed changed from '{old_status}' to '{new_status}'",
        )


def build_edit_link_html(case: Case, url_name: str) -> str:
    """Return html of edit link for case"""
    case_pk: Dict[str, int] = {"pk": case.id}
    edit_url: str = reverse(url_name, kwargs=case_pk)
    return (
        f"<a href='{edit_url}' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


def create_case_and_compliance(**kwargs):
    """Create case and populate compliance fields from arbitrary arguments"""
    compliance_kwargs: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key in COMPLIANCE_FIELDS
    }
    non_compliance_args: Dict[str, Any] = {
        key: value for key, value in kwargs.items() if key not in COMPLIANCE_FIELDS
    }
    case: Case = Case.objects.create(**non_compliance_args)
    if compliance_kwargs:
        for key, value in compliance_kwargs.items():
            setattr(case.compliance, key, value)
        case.compliance.save()
        case.save()
    return case
