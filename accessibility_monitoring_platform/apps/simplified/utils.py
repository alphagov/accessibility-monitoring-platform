"""
Utility functions for cases app
"""

import copy
import json
from collections.abc import Callable
from datetime import date, timedelta
from functools import partial
from typing import Any

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.http import StreamingHttpResponse
from django.urls import reverse

from ..audits.models import Audit
from ..cases.csv_export import csv_output_generator
from ..cases.utils import CaseDetailPage, CaseDetailSection
from ..common.form_extract_utils import (
    FieldLabelAndValue,
    extract_form_labels_and_values,
)
from ..common.sitemap import PlatformPageGroup, Sitemap
from ..common.utils import diff_model_fields
from ..reports.utils import build_issues_tables
from .csv_export import (
    SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
    SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from .models import (
    COMPLIANCE_FIELDS,
    CaseCompliance,
    CaseEvent,
    SimplifiedCase,
    SimplifiedEventHistory,
)

CASE_FIELD_AND_FILTER_NAMES: list[tuple[str, str]] = [
    ("auditor", "auditor_id"),
    ("reviewer", "reviewer_id"),
    ("status", "casestatus__status"),
    ("sector", "sector_id"),
    ("subcategory", "subcategory_id"),
]


ONE_WEEK_IN_DAYS: int = 7
TWELVE_WEEKS_IN_DAYS: int = 12 * ONE_WEEK_IN_DAYS


def get_simplified_case_detail_sections(
    simplified_case: SimplifiedCase, sitemap: Sitemap
) -> list[CaseDetailSection]:
    """Get sections for case view"""
    get_case_rows: Callable = partial(
        extract_form_labels_and_values, instance=simplified_case
    )
    get_audit_rows: Callable = partial(
        extract_form_labels_and_values, instance=simplified_case.audit
    )
    view_sections: list[CaseDetailSection] = []
    for page_group in sitemap.platform_page_groups:
        if page_group.show and (
            page_group.type == PlatformPageGroup.Type.SIMPLIFIED_CASE_NAV
            or page_group.type == PlatformPageGroup.Type.SIMPLIFIED_CASE_TOOLS
        ):
            case_detail_pages: list[CaseDetailPage] = []
            for page in page_group.pages:
                if page.show:
                    display_fields: list[FieldLabelAndValue] = []
                    if page.case_details_form_class:
                        if page.case_details_form_class._meta.model == SimplifiedCase:
                            display_fields = get_case_rows(
                                form=page.case_details_form_class()
                            )
                        elif page.case_details_form_class._meta.model == Audit:
                            display_fields = get_audit_rows(
                                form=page.case_details_form_class()
                            )
                    if page.case_details_template_name:
                        case_detail_pages.append(
                            CaseDetailPage(
                                page=page,
                                display_fields=display_fields,
                            )
                        )
                    if page.subpages is not None:
                        for subpage in page.subpages:
                            if subpage.case_details_template_name:
                                case_detail_pages.append(
                                    CaseDetailPage(
                                        page=subpage,
                                    )
                                )
            view_sections.append(
                CaseDetailSection(
                    page_group_name=page_group.name, pages=case_detail_pages
                )
            )
    return view_sections


def record_case_event(
    user: User, new_case: SimplifiedCase, old_case: SimplifiedCase | None = None
) -> None:
    """Create a case event based on the changes between the old and new cases"""
    if old_case is None:
        CaseEvent.objects.create(
            simplified_case=new_case,
            done_by=user,
            event_type=CaseEvent.EventType.CREATE,
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
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.AUDITOR,
            message=f"Auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.audit is None and new_case.audit is not None:
        CaseEvent.objects.create(
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CREATE_AUDIT,
            message="Start of test",
        )
    if old_case.report_review_status != new_case.report_review_status:
        old_status: str = old_case.get_report_review_status_display()
        new_status: str = new_case.get_report_review_status_display()
        CaseEvent.objects.create(
            simplified_case=old_case,
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
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.QA_AUDITOR,
            message=f"QA auditor changed from {old_user_name} to {new_user_name}",
        )
    if old_case.report_approved_status != new_case.report_approved_status:
        old_status: str = old_case.get_report_approved_status_display()
        new_status: str = new_case.get_report_approved_status_display()
        CaseEvent.objects.create(
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.APPROVE_REPORT,
            message=f"QA approval changed from '{old_status}' to '{new_status}'",
        )
    if old_case.is_ready_for_final_decision != new_case.is_ready_for_final_decision:
        old_status: str = old_case.get_is_ready_for_final_decision_display()
        new_status: str = new_case.get_is_ready_for_final_decision_display()
        CaseEvent.objects.create(
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.READY_FOR_FINAL_DECISION,
            message=f"Case ready for final decision changed from '{old_status}' to '{new_status}'",
        )
    if old_case.case_completed != new_case.case_completed:
        old_status: str = old_case.get_case_completed_display()
        new_status: str = new_case.get_case_completed_display()
        CaseEvent.objects.create(
            simplified_case=old_case,
            done_by=user,
            event_type=CaseEvent.EventType.CASE_COMPLETED,
            message=f"Case completed changed from '{old_status}' to '{new_status}'",
        )


def build_edit_link_html(simplified_case: SimplifiedCase, url_name: str) -> str:
    """Return html of edit link for case"""
    case_pk: dict[str, int] = {"pk": simplified_case.id}
    edit_url: str = reverse(url_name, kwargs=case_pk)
    return (
        f"<a href='{edit_url}' class='govuk-link govuk-link--no-visited-state'>Edit</a>"
    )


def create_case_and_compliance(**kwargs) -> SimplifiedCase:
    """Create case and populate compliance fields from arbitrary arguments"""
    compliance_kwargs: dict[str, Any] = {
        key: value for key, value in kwargs.items() if key in COMPLIANCE_FIELDS
    }
    non_compliance_args: dict[str, Any] = {
        key: value for key, value in kwargs.items() if key not in COMPLIANCE_FIELDS
    }
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        **non_compliance_args
    )
    CaseCompliance.objects.create(simplified_case=simplified_case)
    if compliance_kwargs:
        for key, value in compliance_kwargs.items():
            setattr(simplified_case.compliance, key, value)
        simplified_case.compliance.save()
        simplified_case.save()
    return simplified_case


def record_simplified_model_update_event(
    user: User,
    model_object: models.Model,
    simplified_case: SimplifiedCase,
) -> None:
    """Record model update event"""
    previous_object = model_object.__class__.objects.get(pk=model_object.id)
    previous_object_fields = copy.copy(vars(previous_object))
    del previous_object_fields["_state"]
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    diff_fields: dict[str, Any] = diff_model_fields(
        old_fields=previous_object_fields, new_fields=model_object_fields
    )
    if diff_fields:
        SimplifiedEventHistory.objects.create(
            simplified_case=simplified_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def record_simplified_model_create_event(
    user: User,
    model_object: models.Model,
    simplified_case: SimplifiedCase,
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    SimplifiedEventHistory.objects.create(
        simplified_case=simplified_case,
        created_by=user,
        parent=model_object,
        event_type=SimplifiedEventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def download_simplified_cases(
    simplified_cases: QuerySet[SimplifiedCase], filename: str = "simplified_cases.csv"
) -> StreamingHttpResponse:
    """Given a SimplifiedCase queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=simplified_cases,
            columns_for_export=SIMPLIFIED_CASE_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_simplified_feedback_survey_cases(
    cases: QuerySet[SimplifiedCase],
    filename: str = "simplified_feedback_survey_cases.csv",
) -> StreamingHttpResponse:
    """
    Given a SimplifiedCase queryset, download the feedback survey data in csv format
    """
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=SIMPLIFIED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def get_email_template_context(simplified_case: SimplifiedCase) -> dict[str, Any]:
    """Collect data to add to context of email template previews"""
    context: dict[str, Any] = {}
    context["12_weeks_from_today"] = date.today() + timedelta(days=TWELVE_WEEKS_IN_DAYS)
    context["case"] = simplified_case
    context["retest"] = simplified_case.retests.first()
    if simplified_case.audit is not None:
        context["issues_tables"] = build_issues_tables(
            pages=simplified_case.audit.testable_pages,
            check_results_attr="unfixed_check_results",
        )
        context["retest_issues_tables"] = build_issues_tables(
            pages=simplified_case.audit.retestable_pages,
            use_retest_notes=True,
            check_results_attr="unfixed_check_results",
        )
    return context
