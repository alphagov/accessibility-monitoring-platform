"""
Utils for detailed Case app
"""

import copy
import json
from collections.abc import Callable
from functools import partial
from typing import Any

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.http import StreamingHttpResponse

from ..cases.csv_export import csv_output_generator
from ..cases.models import BaseCase
from ..cases.utils import CaseDetailPage, CaseDetailSection
from ..common.form_extract_utils import (
    FieldLabelAndValue,
    extract_form_labels_and_values,
)
from ..common.sitemap import PlatformPageGroup, Sitemap
from ..common.utils import diff_model_fields
from .csv_export import (
    DETAILED_CASE_COLUMNS_FOR_EXPORT,
    DETAILED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
    DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
)
from .models import DetailedCase, DetailedCaseHistory, DetailedEventHistory


def record_detailed_model_create_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    DetailedEventHistory.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        parent=model_object,
        event_type=DetailedEventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_detailed_model_update_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
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
        DetailedEventHistory.objects.create(
            detailed_case=detailed_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def add_to_detailed_case_history(
    detailed_case: DetailedCase,
    user: User,
    value: str,
    event_type: DetailedCaseHistory.EventType = DetailedCaseHistory.EventType.NOTE,
) -> None:
    """Add latest change of DetailedCase.status to history"""
    detailed_case_history: DetailedCaseHistory = DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=event_type,
        created_by=user,
        value=value,
    )
    record_detailed_model_create_event(
        user=user, model_object=detailed_case_history, detailed_case=detailed_case
    )


def download_detailed_cases(
    detailed_cases: QuerySet[BaseCase], filename: str = "detailed_cases.csv"
) -> StreamingHttpResponse:
    """Given a DetailedCase queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=detailed_cases,
            columns_for_export=DETAILED_CASE_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_detailed_feedback_survey_cases(
    cases: QuerySet[BaseCase], filename: str = "detailed_feedback_survey_cases.csv"
) -> StreamingHttpResponse:
    """
    Given a DetailedCase queryset, download the feedback survey data in csv format
    """
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=DETAILED_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def get_detailed_case_detail_sections(
    detailed_case: DetailedCase, sitemap: Sitemap
) -> list[CaseDetailSection]:
    """Get sections for case view"""
    get_case_rows: Callable = partial(
        extract_form_labels_and_values, instance=detailed_case
    )
    view_sections: list[CaseDetailSection] = []
    for page_group in sitemap.platform_page_groups:
        if page_group.show and (
            page_group.type == PlatformPageGroup.Type.DETAILED_CASE_NAV
            or page_group.type == PlatformPageGroup.Type.DETAILED_CASE_TOOLS
        ):
            case_detail_pages: list[CaseDetailPage] = []
            if page_group.pages is not None:
                for page in page_group.pages:
                    if page.show:
                        display_fields: list[FieldLabelAndValue] = []
                        if page.case_details_form_class:
                            if page.case_details_form_class._meta.model == DetailedCase:
                                display_fields = get_case_rows(
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


def download_detailed_equality_body_cases(
    cases: QuerySet[DetailedCase],
    filename: str = "detailed_equality_body_cases.csv",
) -> StreamingHttpResponse:
    """
    Given a DetailedCase queryset, download the feedback survey data in csv format
    """
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=DETAILED_EQUALITY_BODY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
