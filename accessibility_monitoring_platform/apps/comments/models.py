"""Models for comment and comment history"""

import re
from html import escape

import markdown
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..audits.models import CheckResult, StatementCheck, StatementCheckResult
from ..cases.models import Case
from ..common.utils import replace_whole_words, undo_double_escapes
from ..simplified.models import SimplifiedCase


def get_initial_check_result_url_from_issue_identifier(issue_identifier: str) -> str:
    try:
        check_result: CheckResult = CheckResult.objects.get(
            issue_identifier=issue_identifier
        )
        url: str = reverse(
            "audits:edit-audit-page-checks",
            kwargs={"pk": check_result.page.id},
        )
    except CheckResult.DoesNotExist:
        url: str = ""
    return url


def get_initial_statement_check_result_url_from_issue_identifier(
    issue_identifier: str,
) -> str:
    try:
        statement_check_result: StatementCheckResult = StatementCheckResult.objects.get(
            issue_identifier=issue_identifier
        )
        if statement_check_result.type == StatementCheck.Type.TWELVE_WEEK:
            return ""
        url: str = reverse(
            f"audits:edit-statement-{statement_check_result.type}",
            kwargs={"pk": statement_check_result.audit.id},
        )
    except StatementCheckResult.DoesNotExist:
        url: str = ""
    return url


class Comment(models.Model):
    """Comment model"""

    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name="comment_case",
        blank=True,
        null=True,
    )
    simplified_case = models.ForeignKey(
        SimplifiedCase,
        on_delete=models.PROTECT,
        related_name="comment_simplifiedcase",
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="poster_user",
        blank=True,
        null=True,
    )
    body = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: list[str] = ["created_date"]

    def __str__(self) -> str:
        return f"Comment {self.id} by {self.user}"

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    @property
    def body_html_with_issue_identifier_links(self) -> str:
        html: str = markdown.markdown(
            escape(self.body),
            extensions=settings.MARKDOWN_EXTENSIONS,
        )
        issue_identifiers = set(
            re.findall(f"{self.simplified_case.case_number}-(?:A|S|SC)-[0-9]+", html)
        )
        for issue_identifier in issue_identifiers:
            url: str = ""
            if issue_identifier.startswith(f"{self.simplified_case.case_number}-A-"):
                url: str = get_initial_check_result_url_from_issue_identifier(
                    issue_identifier=issue_identifier
                )
            elif issue_identifier.startswith(f"{self.simplified_case.case_number}-S"):
                url: str = get_initial_statement_check_result_url_from_issue_identifier(
                    issue_identifier=issue_identifier
                )
            if url:
                html = replace_whole_words(
                    old_word=issue_identifier,
                    replacement=f'<a href="{url}#{issue_identifier}" class="govuk-link govuk-link--no-visited-state" target="_blank">{issue_identifier}</a>',
                    string=html,
                )
        return mark_safe(undo_double_escapes(html))
