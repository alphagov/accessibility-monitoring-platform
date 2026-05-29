"""
Tests for cases models
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from ...audits.models import (
    StatementAudit,
    StatementCheck,
    StatementCheckResultInitial,
    WcagAudit,
    WcagCheckResultInitial,
)
from ...audits.tests.create_test_data import (
    create_initial_statement_audit,
    create_initial_wcag_audit,
)
from ...detailed.models import DetailedCase
from ...mobile.models import MobileCase
from ...simplified.models import SimplifiedCase
from ..models import (
    Comment,
    get_initial_check_result_url_from_issue_identifier,
    get_initial_statement_check_result_url_from_issue_identifier,
)

DATETIME_COMMENT_UPDATED: datetime = datetime(2021, 9, 26, tzinfo=timezone.utc)


@pytest.mark.django_db
def test_comment_updated_updated():
    """Test the comment updated field is updated"""
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    comment: Comment = Comment.objects.create(base_case=simplified_case)

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
    simplified_case: SimplifiedCase = SimplifiedCase.objects.create()
    body: str = (
        f"{simplified_case.case_number}-A-1 {simplified_case.case_number}-S-1 {simplified_case.case_number}-SC-1"
    )
    comment: Comment = Comment.objects.create(base_case=simplified_case, body=body)

    assert comment.body_html_with_issue_identifier_links == f"<p>{body}</p>"


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_matching_check_result():
    """
    Test the comment body_html_with_issue_identifier_links converts issue identifier
    to link to initial check result page for matching issue.
    """
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    simplified_case: SimplifiedCase = wcag_audit.simplified_case
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=wcag_audit,
        ).first()
    )
    body: str = (
        f"{wcag_check_result_initial.issue_identifier} {simplified_case.case_number}-S-2 {simplified_case.case_number}-SC-2"
    )
    comment: Comment = Comment.objects.create(base_case=simplified_case, body=body)

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
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    simplified_case: SimplifiedCase = wcag_audit.simplified_case
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(
            wcag_audit=wcag_audit,
        ).first()
    )
    body: str = (
        f"{wcag_check_result_initial.issue_identifier} {wcag_check_result_initial.issue_identifier}99"
    )
    comment: Comment = Comment.objects.create(base_case=simplified_case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p><a href="/audits/pages/1/edit-audit-page-checks/#1-A-1" class="govuk-link govuk-link--no-visited-state" target="_blank">1-A-1</a> 1-A-199</p>'
    )


@pytest.mark.django_db
def test_body_html_with_issue_identifier_links_matching_statement_check_result():
    """
    Test the comment body_html_with_issue_identifier_links converts issue identifier
    to link to initial statement check result page for matching issue.
    """
    statement_audit: StatementAudit = create_initial_statement_audit()
    simplified_case: SimplifiedCase = statement_audit.simplified_case
    statement_check: StatementCheck = StatementCheck.objects.all().first()
    statement_check_result: StatementCheckResultInitial = (
        StatementCheckResultInitial.objects.create(
            statement_audit=statement_audit,
            type=statement_check.type,
            statement_check=statement_check,
        )
    )
    body: str = (
        f"{simplified_case.case_number}-A-2 {statement_check_result.issue_identifier} {simplified_case.case_number}-SC-2"
    )
    comment: Comment = Comment.objects.create(base_case=simplified_case, body=body)

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
    statement_audit: StatementAudit = create_initial_statement_audit()
    simplified_case: SimplifiedCase = statement_audit.simplified_case
    statement_check_result: StatementCheckResultInitial = (
        StatementCheckResultInitial.objects.create(
            statement_audit=statement_audit,
        )
    )
    body: str = (
        f"{simplified_case.case_number}-A-2 {simplified_case.case_number}-S-2 {statement_check_result.issue_identifier}"
    )
    comment: Comment = Comment.objects.create(base_case=simplified_case, body=body)

    assert (
        comment.body_html_with_issue_identifier_links
        == '<p>1-A-2 1-S-2 <a href="/audits/1/edit-statement-custom/#1-SC-2" class="govuk-link govuk-link--no-visited-state" target="_blank">1-SC-2</a></p>'
    )


@pytest.mark.django_db
def test_get_initial_check_result_url_from_issue_identifier():
    """Test expected check result url found from issue identifier"""
    wcag_audit: WcagAudit = create_initial_wcag_audit()
    wcag_check_result_initial: WcagCheckResultInitial = (
        WcagCheckResultInitial.objects.filter(wcag_audit=wcag_audit).first()
    )

    assert (
        get_initial_check_result_url_from_issue_identifier(
            issue_identifier=wcag_check_result_initial.issue_identifier
        )
        == "/audits/pages/1/edit-audit-page-checks/"
    )


@pytest.mark.django_db
def test_get_initial_statement_check_result_url_from_issue_identifier():
    """Test expected statement check result url found from issue identifier"""
    statement_audit: StatementAudit = create_initial_statement_audit()
    for statement_check_type in StatementCheck.Type:
        if statement_check_type == StatementCheck.Type.TWELVE_WEEK:
            continue  # Issues added at 12-weeks don't appear in initial results
        statement_check: StatementCheck = StatementCheck.objects.filter(
            type=statement_check_type
        ).first()
        statement_check_result: StatementCheckResultInitial = (
            StatementCheckResultInitial.objects.create(
                statement_audit=statement_audit,
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


@pytest.mark.parametrize(
    "case_model, expected_absolute_url",
    [
        (DetailedCase, "/comments/1/edit-qa-comment-detailed/"),
        (MobileCase, "/comments/1/edit-qa-comment-mobile/"),
        (SimplifiedCase, "/comments/1/edit-qa-comment-simplified/"),
    ],
)
@pytest.mark.django_db
def test_comment_get_absolute_url(case_model, expected_absolute_url):
    """Test the comment absolute URL is determined by the base case testing type"""
    case: SimplifiedCase | DetailedCase | MobileCase = case_model.objects.create()
    comment: Comment = Comment.objects.create(base_case=case)

    assert comment.get_absolute_url() == expected_absolute_url
