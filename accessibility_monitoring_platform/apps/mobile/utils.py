"""
Utils for mobile Case app
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
    MOBILE_CASE_COLUMNS_FOR_EXPORT,
    MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
    csv_mobile_equality_body_output_generator,
)
from .models import EventHistory, MobileCase, MobileCaseHistory


def record_mobile_model_create_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    EventHistory.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        parent=model_object,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_mobile_model_update_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
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
        EventHistory.objects.create(
            mobile_case=mobile_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def add_to_mobile_case_history(
    mobile_case: MobileCase,
    user: User,
    value: str,
    event_type: MobileCaseHistory.EventType = MobileCaseHistory.EventType.NOTE,
) -> None:
    """Add latest change of MobileCase.status to history"""
    mobile_case_history: MobileCaseHistory = MobileCaseHistory.objects.create(
        mobile_case=mobile_case,
        event_type=event_type,
        created_by=user,
        value=value,
    )
    record_mobile_model_create_event(
        user=user, model_object=mobile_case_history, mobile_case=mobile_case
    )


def download_mobile_cases(
    mobile_cases: QuerySet[BaseCase], filename: str = "mobile_cases.csv"
) -> StreamingHttpResponse:
    """Given a MobileCase queryset, download the data in csv format"""

    response = StreamingHttpResponse(
        csv_output_generator(
            cases=mobile_cases,
            columns_for_export=MOBILE_CASE_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def download_mobile_feedback_survey_cases(
    cases: QuerySet[BaseCase], filename: str = "mobile_feedback_survey_cases.csv"
) -> StreamingHttpResponse:
    """
    Given a MobileCase queryset, download the feedback survey data in csv format
    """
    response = StreamingHttpResponse(
        csv_output_generator(
            cases=cases,
            columns_for_export=MOBILE_FEEDBACK_SURVEY_COLUMNS_FOR_EXPORT,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def get_mobile_case_detail_sections(
    mobile_case: MobileCase, sitemap: Sitemap
) -> list[CaseDetailSection]:
    """Get sections for case view"""
    get_case_rows: Callable = partial(
        extract_form_labels_and_values, instance=mobile_case
    )
    view_sections: list[CaseDetailSection] = []
    for page_group in sitemap.platform_page_groups:
        if page_group.show and (
            page_group.type == PlatformPageGroup.Type.MOBILE_CASE_NAV
            or page_group.type == PlatformPageGroup.Type.MOBILE_CASE_TOOLS
        ):
            case_detail_pages: list[CaseDetailPage] = []
            for page in page_group.pages:
                if page.show:
                    display_fields: list[FieldLabelAndValue] = []
                    if page.case_details_form_class:
                        if page.case_details_form_class._meta.model == MobileCase:
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


def download_mobile_equality_body_cases(
    mobile_cases: QuerySet[MobileCase],
    filename: str = "mobile_equality_body_cases.csv",
) -> StreamingHttpResponse:
    """
    Given a MobileCase queryset, download the feedback survey data in csv format
    """
    response = StreamingHttpResponse(
        csv_mobile_equality_body_output_generator(
            mobile_cases=mobile_cases,
        ),
        content_type="text/csv",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
