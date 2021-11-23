"""
Utilities for audits app
"""

from typing import List, Union

from django.contrib.auth.models import User

from ..common.utils import record_model_create_event
from .models import (
    Audit,
    Page,
    WcagDefinition,
    CheckResult,
    MANDATORY_PAGE_TYPES,
    PAGE_TYPE_HOME,
    PAGE_TYPE_PDF,
    TEST_TYPE_PDF,
    TEST_TYPE_MANUAL,
)


def create_pages_and_tests_for_new_audit(audit: Audit, user: User) -> None:
    """
    Create mandatory pages for new audit.
    Create Wcag tests from WcagDefinition metadata for new audit.
    """
    pdf_wcag_definitons: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_PDF)
    )
    manual_wcag_definitions: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_MANUAL)
    )

    home_page: Union[Page, None] = None  # type: ignore
    for page_type in MANDATORY_PAGE_TYPES:
        page: Page = Page.objects.create(audit=audit, type=page_type)  # type: ignore
        record_model_create_event(user=user, model_object=page)  # type: ignore
        wcag_definitons: List[WcagDefinition] = (
            pdf_wcag_definitons
            if page_type == PAGE_TYPE_PDF
            else manual_wcag_definitions
        )
        for wcag_definition in wcag_definitons:
            check_result: CheckResult = CheckResult.objects.create(
                audit=audit,  # type: ignore
                page=page,
                type=wcag_definition.type,
                wcag_definition=wcag_definition,
            )
            record_model_create_event(user=user, model_object=check_result)  # type: ignore
        if page_type == PAGE_TYPE_HOME:
            home_page: Page = page
    audit.next_page = home_page  # type: ignore
    audit.save()


def create_check_results_for_new_page(page: Page, user: User) -> None:
    """
    Create mandatory check results for new page from WcagDefinition metadata.
    """
    manual_wcag_definitions: List[WcagDefinition] = list(
        WcagDefinition.objects.filter(type=TEST_TYPE_MANUAL)
    )

    for wcag_definition in manual_wcag_definitions:
        check_result: CheckResult = CheckResult.objects.create(
            audit=page.audit,
            page=page,
            type=wcag_definition.type,
            wcag_definition=wcag_definition,
        )
        record_model_create_event(user=user, model_object=check_result)  # type: ignore
