"""
Tests for cases models
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from ...audits.models import (
    Audit,
    CheckResult,
    Page,
    StatementCheck,
    StatementCheckResult,
    WcagDefinition,
)
from ...cases.models import Case
from ..models import (
    Comment,
    get_initial_check_result_url_from_issue_identifier,
    get_initial_statement_check_result_url_from_issue_identifier,
)

DATETIME_COMMENT_UPDATED: datetime = datetime(2021, 9, 26, tzinfo=timezone.utc)


@pytest.mark.django_db
def test_comment_updated_updated():
    """Test the comment updated field is updated"""
    case: Case = Case.objects.create()
    comment: Comment = Comment.objects.create(case=case)

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_UPDATED)
    ):
        comment.save()

    assert comment.updated == DATETIME_COMMENT_UPDATED


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_no_matching_issues():
    """
    Test the comment body_html_with_issue_identifier_links does not change issue
    identifiers with no matching issues.
    """
    case: Case = Case.objects.create()
    body: str = f"{case.case_number}-A-1 {case.case_number}-S-1 {case.case_number}-SC-1"
    comment: Comment = Comment.objects.create(case=case, body=body)

    assert comment.body_html_with_issue_identifier_links == f"<p>{body}</p>"


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_matching_check_result():
    """
    Test the comment body_html_with_issue_identifier_links converts issue identifier
    to link to initial check result page for matching issue.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name="WCAG definition"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    body: str = (
        f"{check_result.issue_identifier} {case.case_number}-S-2 {case.case_number}-SC-2"
    )
    comment: Comment = Comment.objects.create(case=case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p><a href="/audits/pages/1/edit-audit-page-checks/#1-A-1" class="govuk-link govuk-link--no-visited-state" target="_blank">1-A-1</a> 1-S-2 1-SC-2</p>'
    )


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_longer_issue_identifier():
    """
    Test the comment body_html_with_issue_identifier_links does not convert longer issue
    identifier to link.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name="WCAG definition"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )
    body: str = f"{check_result.issue_identifier} {check_result.issue_identifier}1"
    comment: Comment = Comment.objects.create(case=case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p><a href="/audits/pages/1/edit-audit-page-checks/#1-A-1" class="govuk-link govuk-link--no-visited-state" target="_blank">1-A-1</a> 1-A-11</p>'
    )


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_matching_statement_check_result():
    """
    Test the comment body_html_with_issue_identifier_links converts issue identifier
    to link to initial statement check result page for matching issue.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
        type=statement_check.type,
        statement_check=statement_check,
    )
    body: str = (
        f"{case.case_number}-A-2 {statement_check_result.issue_identifier} {case.case_number}-SC-2"
    )
    comment: Comment = Comment.objects.create(case=case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p>1-A-2 <a href="/audits/1/edit-statement-overview/#1-S-1" class="govuk-link govuk-link--no-visited-state" target="_blank">1-S-1</a> 1-SC-2</p>'
    )


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_matching_custom_statement_check_result():
    """
    Test the comment body_html_with_issue_identifier_links converts issue identifier
    to link to initial custom statement check result page for matching issue.
    """
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    statement_check_result: StatementCheckResult = StatementCheckResult.objects.create(
        audit=audit,
    )
    body: str = (
        f"{case.case_number}-A-2 {case.case_number}-S-2 {statement_check_result.issue_identifier}"
    )
    comment: Comment = Comment.objects.create(case=case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p>1-A-2 1-S-2 <a href="/audits/1/edit-statement-custom/#1-SC-1" class="govuk-link govuk-link--no-visited-state" target="_blank">1-SC-1</a></p>'
    )


@pytest.mark.django_db
def test_get_initial_check_result_url_from_issue_identifier():
    """Test expected check result url found from issue identifier"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    page: Page = Page.objects.create(audit=audit, url="https://example.com")
    wcag_definition: WcagDefinition = WcagDefinition.objects.create(
        type=WcagDefinition.Type.AXE, name="WCAG definition"
    )
    check_result: CheckResult = CheckResult.objects.create(
        audit=audit,
        page=page,
        type=wcag_definition.type,
        wcag_definition=wcag_definition,
    )

    assert (
        get_initial_check_result_url_from_issue_identifier(
            issue_identifier=check_result.issue_identifier
        )
        == "/audits/pages/1/edit-audit-page-checks/"
    )


@pytest.mark.django_db
def test_get_initial_statement_check_result_url_from_issue_identifier():
    """Test expected statement check result url found from issue identifier"""
    case: Case = Case.objects.create()
    audit: Audit = Audit.objects.create(case=case)
    for statement_check_type in StatementCheck.Type:
        if statement_check_type == StatementCheck.Type.TWELVE_WEEK:
            continue  # Issues added at 12-weeks don't appear in initial results
        statement_check: StatementCheck = StatementCheck.objects.filter(
            type=statement_check_type
        ).first()
        statement_check_result: StatementCheckResult = (
            StatementCheckResult.objects.create(
                audit=audit,
                type=statement_check_type,
                statement_check=statement_check,
            )
        )

        assert (
            get_initial_statement_check_result_url_from_issue_identifier(
                issue_identifier=statement_check_result.issue_identifier
            )
            == f"/audits/1/edit-statement-{statement_check_type}/"
        )
