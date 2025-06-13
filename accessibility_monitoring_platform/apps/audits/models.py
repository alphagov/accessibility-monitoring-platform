"""
Models - audits (called tests by the users)
"""

from __future__ import annotations

from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case as DjangoCase
from django.db.models import Max, Q, When
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..cases.models import Case
from ..common.models import Boolean, StartEndDateManager, VersionModel
from ..common.utils import amp_format_date, calculate_percentage
from ..simplified.models import CaseCompliance, SimplifiedCase

ISSUE_IDENTIFIER_WCAG: str = "A"
ISSUE_IDENTIFIER_STATEMENT: str = "S"


def build_issue_identifier(
    simplified_case: SimplifiedCase,
    issue: (
        CheckResult
        | StatementCheckResult
        | RetestCheckResult
        | RetestStatementCheckResult
    ),
    custom_issue: bool = False,
) -> str:
    """Format and return issue identifier"""
    issue_type: str = (
        ISSUE_IDENTIFIER_WCAG
        if isinstance(issue, (CheckResult, RetestCheckResult))
        else ISSUE_IDENTIFIER_STATEMENT
    )
    if custom_issue:
        issue_type += "C"
    return f"{simplified_case.case_number}-{issue_type}-{issue.id_within_case}"


class Audit(VersionModel):
    """
    Model for test
    """

    class ScreenSize(models.TextChoices):
        SIZE_13 = "13in", "13 inch"
        SIZE_14 = "14in", "14 inch"
        SIZE_15 = "15in", "15 inch"

    class Exemptions(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Unknown"

    class DisproportionateBurden(models.TextChoices):
        NO_ASSESSMENT = "no-assessment", "Claim with no assessment"
        ASSESSMENT = "assessment", "Claim with assessment"
        NO_CLAIM = "no-claim", "No claim"
        NO_STATEMENT = "no-statement", "No statement"
        NOT_CHECKED = "not-checked", "Not checked"

    case = models.OneToOneField(
        Case,
        on_delete=models.PROTECT,
        related_name="audit_case",
        blank=True,
        null=True,
    )
    simplified_case = models.OneToOneField(
        SimplifiedCase,
        on_delete=models.PROTECT,
        related_name="audit_simplifiedcase",
        blank=True,
        null=True,
    )
    published_report_data_updated_time = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    # metadata page
    date_of_test = models.DateField(default=date.today)
    screen_size = models.CharField(
        max_length=20,
        choices=ScreenSize.choices,
        default=ScreenSize.SIZE_13,
    )
    exemptions_state = models.CharField(
        max_length=20,
        choices=Exemptions.choices,
        default=Exemptions.UNKNOWN,
    )
    exemptions_notes = models.TextField(default="", blank=True)
    audit_metadata_complete_date = models.DateField(null=True, blank=True)

    # Pages page
    audit_pages_complete_date = models.DateField(null=True, blank=True)

    # Website decision
    audit_website_decision_complete_date = models.DateField(null=True, blank=True)

    # Statement decision
    audit_statement_decision_complete_date = models.DateField(null=True, blank=True)

    # WCAG Summary
    audit_wcag_summary_complete_date = models.DateField(null=True, blank=True)

    # Statement Summary
    audit_statement_summary_complete_date = models.DateField(null=True, blank=True)

    # Statement pages
    audit_statement_pages_complete_date = models.DateField(null=True, blank=True)

    # Statement checking overview
    statement_extra_report_text = models.TextField(default="", blank=True)
    audit_statement_overview_complete_date = models.DateField(null=True, blank=True)

    # Statement checking website
    audit_statement_website_complete_date = models.DateField(null=True, blank=True)

    # Statement checking compliance
    audit_statement_compliance_complete_date = models.DateField(null=True, blank=True)

    # Statement checking non-accessible content
    audit_statement_non_accessible_complete_date = models.DateField(
        null=True, blank=True
    )

    # Statement checking preparation
    audit_statement_preparation_complete_date = models.DateField(null=True, blank=True)

    # Statement checking feedback
    audit_statement_feedback_complete_date = models.DateField(null=True, blank=True)

    # Statement checking other
    audit_statement_custom_complete_date = models.DateField(null=True, blank=True)

    # Initial disproportionate burden claim
    initial_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    initial_disproportionate_burden_notes = models.TextField(default="", blank=True)
    initial_disproportionate_burden_complete_date = models.DateField(
        null=True, blank=True
    )

    # Report text
    archive_audit_report_text_complete_date = models.DateField(null=True, blank=True)

    # retest metadata page
    retest_date = models.DateField(null=True, blank=True)
    audit_retest_metadata_notes = models.TextField(default="", blank=True)
    audit_retest_metadata_complete_date = models.DateField(null=True, blank=True)

    # Update page links
    audit_retest_pages_complete_date = models.DateField(null=True, blank=True)

    # Retest website compliance
    audit_retest_website_decision_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest WCAG Summary
    audit_retest_wcag_summary_complete_date = models.DateField(null=True, blank=True)

    # Retest Statement Summary
    audit_retest_statement_summary_complete_date = models.DateField(
        null=True, blank=True
    )

    # 12-week accessibility statement (no initial statement)
    twelve_week_accessibility_statement_url = models.TextField(default="", blank=True)

    # Statement pages
    audit_retest_statement_pages_complete_date = models.DateField(null=True, blank=True)

    # Retest statement checking overview
    audit_retest_statement_overview_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking website
    audit_retest_statement_website_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking compliance
    audit_retest_statement_compliance_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking non-accessible content
    audit_retest_statement_non_accessible_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking preparation
    audit_retest_statement_preparation_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking feedback
    audit_retest_statement_feedback_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement checking other
    audit_retest_statement_custom_complete_date = models.DateField(
        null=True, blank=True
    )

    # 12-week disproportionate burden claim
    twelve_week_disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    twelve_week_disproportionate_burden_notes = models.TextField(default="", blank=True)
    twelve_week_disproportionate_burden_complete_date = models.DateField(
        null=True, blank=True
    )

    # Retest statement comparison
    audit_retest_statement_comparison_complete_date = models.DateField(
        null=True, blank=True
    )
    # Retest statement decision
    audit_retest_statement_decision_complete_date = models.DateField(
        null=True, blank=True
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.case} (Test {amp_format_date(self.date_of_test)})"

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-audit-metadata", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    @property
    def deleted_pages(self):
        return self.page_audit.filter(is_deleted=True)

    @property
    def every_page(self):
        """Sort page of type PDF to be last apart from the accessibility statement"""
        return (
            self.page_audit.filter(is_deleted=False)
            .annotate(
                position_pdfs_statements_last=DjangoCase(
                    When(page_type=Page.Type.PDF, then=1),
                    When(page_type=Page.Type.STATEMENT, then=2),
                    default=0,
                )
            )
            .order_by("position_pdfs_statements_last", "id")
        )

    @property
    def testable_pages(self):
        return self.every_page.exclude(not_found=Boolean.YES).exclude(url="")

    @property
    def retestable_pages(self):
        return self.testable_pages.filter(retest_page_missing_date=None)

    @property
    def html_pages(self):
        return self.every_page.exclude(page_type=Page.Type.PDF)

    @property
    def accessibility_statement_page(self):
        return self.every_page.filter(page_type=Page.Type.STATEMENT).first()

    @property
    def contact_page(self):
        return self.every_page.filter(page_type=Page.Type.CONTACT).first()

    @property
    def standard_pages(self):
        return self.every_page.exclude(page_type=Page.Type.EXTRA)

    @property
    def extra_pages(self):
        return self.html_pages.filter(page_type=Page.Type.EXTRA)

    @property
    def missing_at_retest_pages(self):
        return self.testable_pages.exclude(retest_page_missing_date=None)

    @property
    def missing_at_retest_check_results(self):
        return self.checkresult_audit.filter(
            is_deleted=False,
            check_result_state=CheckResult.Result.ERROR,
            page__in=self.missing_at_retest_pages,
        )

    @property
    def failed_check_results(self):
        return (
            self.checkresult_audit.filter(
                is_deleted=False,
                check_result_state=CheckResult.Result.ERROR,
                page__is_deleted=False,
                page__not_found=Boolean.NO,
                page__retest_page_missing_date=None,
                page__is_contact_page=Boolean.NO,
            )
            .annotate(
                position_pdf_and_statement_page_last=DjangoCase(
                    When(page__page_type=Page.Type.PDF, then=1),
                    When(page__page_type=Page.Type.STATEMENT, then=2),
                    default=0,
                )
            )
            .order_by(
                "position_pdf_and_statement_page_last",
                "page__id",
                "wcag_definition__id",
            )
            .select_related("page", "wcag_definition")
            .all()
        )

    @property
    def fixed_check_results(self):
        return self.failed_check_results.filter(
            retest_state=CheckResult.RetestResult.FIXED
        )

    @property
    def unfixed_check_results(self):
        return self.failed_check_results.exclude(
            retest_state=CheckResult.RetestResult.FIXED
        )

    @property
    def percentage_wcag_issues_fixed(self) -> int:
        return calculate_percentage(
            total=self.failed_check_results.count(),
            partial=self.fixed_check_results.count(),
        )

    @property
    def statement_check_results(self):
        return self.statementcheckresult_set.filter(is_deleted=False)

    @property
    def overview_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.OVERVIEW)

    @property
    def statement_found_check(self):
        return self.overview_statement_check_results.first()

    @property
    def statement_structure_check(self):
        return self.overview_statement_check_results.last()

    @property
    def overview_statement_checks_complete(self) -> bool:
        return (
            self.overview_statement_check_results.filter(
                check_result_state=StatementCheckResult.Result.NOT_TESTED
            ).count()
            == 0
        )

    @property
    def statement_check_result_statement_found(self) -> bool:
        overview_statement_yes_count: CheckResult = (
            self.overview_statement_check_results.filter(
                check_result_state=StatementCheckResult.Result.YES
            ).count()
        )
        return (
            overview_statement_yes_count
            == self.overview_statement_check_results.count()
        )

    @property
    def website_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.WEBSITE)

    @property
    def compliance_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.COMPLIANCE)

    @property
    def non_accessible_statement_check_results(self):
        return self.statement_check_results.filter(
            type=StatementCheck.Type.NON_ACCESSIBLE
        )

    @property
    def preparation_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.PREPARATION)

    @property
    def feedback_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.FEEDBACK)

    @property
    def custom_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.CUSTOM)

    @property
    def new_12_week_custom_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.TWELVE_WEEK)

    @property
    def failed_statement_check_results(self):
        return self.statement_check_results.filter(
            check_result_state=StatementCheckResult.Result.NO
        )

    @property
    def passed_statement_check_results(self):
        return self.statement_check_results.filter(
            check_result_state=StatementCheckResult.Result.YES
        )

    @property
    def outstanding_statement_check_results(self):
        return self.statement_check_results.filter(
            Q(check_result_state=StatementCheckResult.Result.NO)
            | Q(retest_state=StatementCheckResult.Result.NO)
            | Q(statement_check=None)
        ).exclude(retest_state=StatementCheckResult.Result.YES)

    @property
    def overview_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.OVERVIEW
        )

    @property
    def website_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.WEBSITE
        )

    @property
    def compliance_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.COMPLIANCE
        )

    @property
    def non_accessible_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.NON_ACCESSIBLE
        )

    @property
    def preparation_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.PREPARATION
        )

    @property
    def feedback_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.FEEDBACK
        )

    @property
    def custom_outstanding_statement_check_results(self):
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.CUSTOM
        )

    @property
    def all_overview_statement_checks_have_passed(self) -> bool:
        """Check all overview statement checks have passed test or retest"""
        return (
            self.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResult.Result.YES
            ).count()
            == 0
            or self.overview_statement_check_results.exclude(
                retest_state=StatementCheckResult.Result.YES
            ).count()
            == 0
        )

    @property
    def statement_initially_found(self) -> bool:
        """Check an accesibility statement was initially found"""
        return (
            self.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResult.Result.YES
            ).count()
            == 0
        )

    @property
    def statement_found_at_12_week_retest(self) -> bool:
        """Check an accessibility statement was found at 12-week retest"""
        return (
            self.overview_statement_check_results.exclude(
                retest_state=StatementCheckResult.Result.YES
            ).count()
            == 0
        )

    @property
    def failed_retest_statement_check_results(self):
        return self.statement_check_results.filter(
            retest_state=StatementCheckResult.Result.NO
        )

    @property
    def passed_retest_statement_check_results(self):
        return self.statement_check_results.filter(
            retest_state=StatementCheckResult.Result.YES
        )

    @property
    def fixed_statement_check_results(self):
        return self.failed_statement_check_results.filter(
            retest_state=StatementCheckResult.Result.YES
        )

    @property
    def statement_pages(self):
        return self.statementpage_set.filter(is_deleted=False)

    @property
    def latest_statement_link(self) -> str | None:
        for statement_page in self.statement_pages:
            if statement_page.url:
                return statement_page.url

    @property
    def accessibility_statement_initially_found(self) -> bool:
        return (
            self.statement_pages.filter(
                added_stage=StatementPage.AddedStage.INITIAL
            ).count()
            > 0
        )

    @property
    def twelve_week_accessibility_statement_found(self) -> bool:
        return (
            self.statement_pages.filter(
                added_stage=StatementPage.AddedStage.TWELVE_WEEK
            ).count()
            > 0
        )

    @property
    def accessibility_statement_found(self) -> bool:
        return self.statement_pages.count() > 0 and self.latest_statement_link != ""


class Page(models.Model):
    """
    Model for test/audit page
    """

    class Type(models.TextChoices):
        EXTRA = "extra", "Additional"
        HOME = "home", "Home"
        CONTACT = "contact", "Contact"
        STATEMENT = "statement", "Accessibility statement"
        CORONAVIRUS = "coronavirus", "Coronavirus"
        PDF = "pdf", "PDF"
        FORM = "form", "Form"

    MANDATORY_PAGE_TYPES: list[str] = [
        Type.HOME,
        Type.CONTACT,
        Type.STATEMENT,
        Type.PDF,
        Type.FORM,
    ]
    audit = models.ForeignKey(
        Audit, on_delete=models.PROTECT, related_name="page_audit"
    )
    is_deleted = models.BooleanField(default=False)

    page_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.EXTRA
    )
    name = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    updated_url = models.TextField(default="", blank=True)
    location = models.TextField(default="", blank=True)
    updated_location = models.TextField(default="", blank=True)
    complete_date = models.DateField(null=True, blank=True)
    no_errors_date = models.DateField(null=True, blank=True)
    not_found = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    is_contact_page = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    retest_complete_date = models.DateField(null=True, blank=True)
    retest_page_missing_date = models.DateField(null=True, blank=True)
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return self.name if self.name else self.get_page_type_display()

    @property
    def page_title(self) -> str:
        title: str = str(self)
        if self.page_type != Page.Type.PDF:
            title += " page"
        return title

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-audit-page-checks", kwargs={"pk": self.pk})

    @property
    def all_check_results(self):
        return (
            self.checkresult_page.filter(is_deleted=False)
            .order_by("wcag_definition__id")
            .select_related("wcag_definition")
            .all()
        )

    @property
    def failed_check_results(self):
        return self.all_check_results.filter(
            check_result_state=CheckResult.Result.ERROR
        )

    @property
    def count_failed_check_results(self):
        return self.failed_check_results.count()

    @property
    def unfixed_check_results(self):
        return self.failed_check_results.exclude(
            retest_state=CheckResult.RetestResult.FIXED
        )

    @property
    def check_results_by_wcag_definition(self):
        check_results: QuerySet[CheckResult] = self.all_check_results
        return {
            check_result.wcag_definition: check_result for check_result in check_results
        }

    @property
    def anchor(self):
        return f"test-page-{self.id}"


class WcagDefinition(models.Model):
    """
    Model for WCAG tests captured by the platform
    """

    class Type(models.TextChoices):
        MANUAL = "manual", "Manual"
        AXE = "axe", "Axe"
        PDF = "pdf", "PDF"

    type = models.CharField(max_length=20, choices=Type.choices, default=Type.MANUAL)
    name = models.TextField(default="", blank=True)
    description = models.TextField(default="", blank=True)
    hint = models.TextField(default="", blank=True)
    url_on_w3 = models.TextField(default="", blank=True)
    report_boilerplate = models.TextField(default="", blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    objects = StartEndDateManager()

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        if self.description:
            return f"{self.name}: {self.description} ({self.get_type_display()})"
        return f"{self.name} ({self.get_type_display()})"

    def get_absolute_url(self) -> str:
        return reverse("audits:wcag-definition-update", kwargs={"pk": self.pk})


class CheckResult(models.Model):
    """
    Model for test result
    """

    class Result(models.TextChoices):
        ERROR = "error", "Error found"
        NO_ERROR = "no-error", "No issue"
        NOT_TESTED = "not-tested", "Not tested"

    class RetestResult(models.TextChoices):
        FIXED = "fixed", "Fixed"
        NOT_FIXED = "not-fixed", "Not fixed"
        NOT_RETESTED = "not-retested", "Not retested"

    audit = models.ForeignKey(
        Audit, on_delete=models.PROTECT, related_name="checkresult_audit"
    )
    page = models.ForeignKey(
        Page, on_delete=models.PROTECT, related_name="checkresult_page"
    )
    id_within_case = models.IntegerField(default=0, blank=True)
    issue_identifier = models.CharField(max_length=20, default="")
    is_deleted = models.BooleanField(default=False)
    type = models.CharField(
        max_length=20,
        choices=WcagDefinition.Type.choices,
        default=WcagDefinition.Type.PDF,
    )
    wcag_definition = models.ForeignKey(
        WcagDefinition,
        on_delete=models.PROTECT,
        related_name="checkresult_wcagdefinition",
    )

    check_result_state = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    notes = models.TextField(default="", blank=True)
    retest_state = models.CharField(
        max_length=20,
        choices=RetestResult.choices,
        default=RetestResult.NOT_RETESTED,
    )
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    @property
    def retest_form_initial(self) -> dict[str, str]:
        return {
            "id": self.id,
            "retest_state": self.retest_state,
            "retest_notes": self.retest_notes,
            "check_result": self,
        }

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=[
                    "issue_identifier",
                ]
            ),
        ]

    def __str__(self) -> str:
        return f"{self.page} | {self.wcag_definition} | {self.issue_identifier}"

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        if not self.id:
            self.id_within_case = self.audit.checkresult_audit.all().count() + 1
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.audit.simplified_case, issue=self
            )
        super().save(*args, **kwargs)

    @property
    def matching_wcag_with_retest_notes_check_results(self) -> dict[str, str]:
        """Other check results with retest notes for matching WCAGDefinition"""
        return (
            self.audit.failed_check_results.filter(wcag_definition=self.wcag_definition)
            .exclude(page=self.page)
            .exclude(retest_notes="")
        )


class CheckResultNotesHistory(models.Model):
    """Model to record history of changes to CheckResult notes"""

    check_result = models.ForeignKey(CheckResult, on_delete=models.PROTECT)
    notes = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.check_result} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Check result notes histories"


class CheckResultRetestNotesHistory(models.Model):
    """Model to record history of changes to CheckResult retest_notes"""

    check_result = models.ForeignKey(CheckResult, on_delete=models.PROTECT)
    retest_notes = models.TextField(default="", blank=True)
    retest_state = models.CharField(
        max_length=20,
        choices=CheckResult.RetestResult.choices,
        default=CheckResult.RetestResult.NOT_RETESTED,
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.check_result} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "Check result retest notes histories"


class StatementCheck(models.Model):
    """
    Model for accessibilty statement-specific checks
    """

    class Type(models.TextChoices):
        OVERVIEW = "overview", "Statement overview"
        WEBSITE = "website", "Statement information"
        COMPLIANCE = "compliance", "Compliance status"
        NON_ACCESSIBLE = "non-accessible", "Non-accessible content"
        PREPARATION = "preparation", "Statement preparation"
        FEEDBACK = "feedback", "Feedback and enforcement procedure"
        CUSTOM = "custom", "Custom statement issues"
        TWELVE_WEEK = "12-week", "New 12-week custom statement issues"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.CUSTOM,
    )
    issue_number = models.IntegerField(default=0, blank=True)
    label = models.TextField(default="", blank=True)
    success_criteria = models.TextField(default="", blank=True)
    report_text = models.TextField(default="", blank=True)
    position = models.IntegerField(default=0)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    objects = StartEndDateManager()

    class Meta:
        ordering = ["position", "id"]

    def __str__(self) -> str:
        if self.success_criteria:
            return f"{self.label}: {self.success_criteria} ({self.get_type_display()})"
        return f"{self.label} ({self.get_type_display()})"

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            self.issue_number = StatementCheck.objects.all().count() + 1
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("audits:statement-check-update", kwargs={"pk": self.pk})


class StatementCheckResult(models.Model):
    """
    Model for accessibility statement-specific check result
    """

    class Result(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        NOT_TESTED = "not-tested", "Not tested"

    audit = models.ForeignKey(Audit, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=0, blank=True)
    issue_identifier = models.CharField(max_length=20, default="")
    statement_check = models.ForeignKey(
        StatementCheck, on_delete=models.PROTECT, null=True, blank=True
    )
    type = models.CharField(
        max_length=20,
        choices=StatementCheck.Type.choices,
        default=StatementCheck.Type.CUSTOM,
    )
    check_result_state = models.CharField(
        max_length=10,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    report_comment = models.TextField(default="", blank=True)
    auditor_notes = models.TextField(default="", blank=True)
    retest_state = models.CharField(
        max_length=10,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    retest_comment = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["statement_check__position", "id"]
        indexes = [
            models.Index(
                fields=[
                    "issue_identifier",
                ]
            ),
        ]

    def __str__(self) -> str:
        if self.statement_check is None:
            return f"{self.audit} | Custom [{self.issue_identifier}]"
        return f"{self.audit} | {self.statement_check} [{self.issue_identifier}]"

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            if self.statement_check:
                self.id_within_case = self.statement_check.issue_number
            else:
                self.id_within_case = self.audit.statement_check_results.count() + 1
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.audit.simplified_case,
                issue=self,
                custom_issue=self.statement_check is None,
            )
        super().save(*args, **kwargs)

    @property
    def label(self):
        return self.statement_check.label if self.statement_check else "Custom"

    @property
    def display_value(self):
        value_str: str = self.get_check_result_state_display()
        if self.report_comment:
            value_str += f"<br><br>Auditor's comment: {self.report_comment}"
        return mark_safe(value_str)

    @property
    def edit_initial_url_name(self) -> str:
        if self.statement_check is None:
            return "audits:edit-statement-custom"
        return f"audits:edit-statement-{self.statement_check.type}"

    @property
    def edit_12_week_url_name(self) -> str:
        if self.statement_check is None:
            return "audits:edit-retest-statement-custom"
        return f"audits:edit-retest-statement-{self.type}"


class Retest(VersionModel):
    """
    Model for retest of outstanding issues requested by an equality body
    """

    class Compliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        PARTIAL = "partially-compliant", "Partially compliant"
        NOT_KNOWN = "not-known", "Not known"

    case = models.ForeignKey(Case, on_delete=models.PROTECT, blank=True, null=True)
    simplified_case = models.ForeignKey(
        SimplifiedCase,
        on_delete=models.PROTECT,
        related_name="retest_simplifiedcase",
        blank=True,
        null=True,
    )
    id_within_case = models.IntegerField(default=1, blank=True)
    date_of_retest = models.DateField(default=date.today)
    retest_notes = models.TextField(default="", blank=True)
    retest_compliance_state = models.CharField(
        max_length=20,
        choices=Compliance.choices,
        default=Compliance.NOT_KNOWN,
    )
    compliance_notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)
    complete_date = models.DateField(null=True, blank=True)
    comparison_complete_date = models.DateField(null=True, blank=True)
    compliance_complete_date = models.DateField(null=True, blank=True)
    statement_pages_complete_date = models.DateField(null=True, blank=True)

    statement_overview_complete_date = models.DateField(null=True, blank=True)
    statement_website_complete_date = models.DateField(null=True, blank=True)
    statement_compliance_complete_date = models.DateField(null=True, blank=True)
    statement_non_accessible_complete_date = models.DateField(null=True, blank=True)
    statement_preparation_complete_date = models.DateField(null=True, blank=True)
    statement_feedback_complete_date = models.DateField(null=True, blank=True)
    statement_custom_complete_date = models.DateField(null=True, blank=True)
    statement_results_complete_date = models.DateField(null=True, blank=True)

    disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=Audit.DisproportionateBurden.choices,
        default=Audit.DisproportionateBurden.NOT_CHECKED,
    )
    disproportionate_burden_notes = models.TextField(default="", blank=True)
    disproportionate_burden_complete_date = models.DateField(null=True, blank=True)

    statement_compliance_state = models.CharField(
        max_length=200,
        choices=CaseCompliance.StatementCompliance.choices,
        default=CaseCompliance.StatementCompliance.UNKNOWN,
    )
    statement_compliance_notes = models.TextField(default="", blank=True)
    statement_decision_complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["case_id", "-id_within_case"]

    def get_absolute_url(self) -> str:
        return reverse("audits:retest-compliance-update", kwargs={"pk": self.id})

    def __str__(self) -> str:
        if self.id_within_case == 0:
            return "12-week retest"
        return f"Retest #{self.id_within_case}"

    @property
    def is_incomplete(self) -> bool:
        return self.retest_compliance_state == Retest.Compliance.NOT_KNOWN

    @property
    def fixed_checks_count(self):
        """
        Add the numbers of checks fixed in the 12-week retest and all equality
        body requested retests up to this one.
        """
        fixed_checks_count: int = (
            CheckResult.objects.filter(audit=self.simplified_case.audit)
            .filter(retest_state=CheckResult.RetestResult.FIXED)
            .exclude(page__not_found="yes")
            .count()
        )
        for retest in self.simplified_case.retests.exclude(
            id_within_case__gt=self.id_within_case
        ).exclude(id_within_case=0):
            fixed_checks_count += (
                RetestCheckResult.objects.filter(retest=retest)
                .filter(retest_state=CheckResult.RetestResult.FIXED)
                .exclude(retest_page__page__not_found="yes")
                .count()
            )
        return fixed_checks_count

    @property
    def original_retest(self):
        """Copy of 12-week retest results"""
        return self.simplified_case.retests.filter(id_within_case=0).first()

    @property
    def previous_retest(self):
        """Return previous retest"""
        if self.id_within_case > 0:
            return self.simplified_case.retests.filter(
                id_within_case=self.id_within_case - 1
            ).first()
        return None

    @property
    def latest_retest(self):
        """Return latest retest"""
        return self.simplified_case.retests.first()

    @property
    def check_results(self):
        return (
            self.retestcheckresult_set.filter(
                retest_page__missing_date=None,
            )
            .annotate(
                position_pdf_and_statement_page_last=DjangoCase(
                    When(retest_page__page__page_type=Page.Type.PDF, then=1), default=0
                )
            )
            .order_by(
                "position_pdf_and_statement_page_last",
                "retest_page__id",
                "check_result__wcag_definition__id",
            )
        )

    @property
    def unfixed_check_results(self):
        return self.check_results.exclude(retest_state=CheckResult.RetestResult.FIXED)

    @property
    def statement_check_results(self):
        return self.reteststatementcheckresult_set.filter(is_deleted=False)

    @property
    def failed_statement_check_results(self):
        return self.statement_check_results.filter(
            check_result_state=StatementCheckResult.Result.NO
        )

    @property
    def overview_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.OVERVIEW)

    @property
    def all_overview_statement_checks_have_passed(self) -> bool:
        """Check all overview statement checks have passed"""
        return (
            self.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResult.Result.YES
            ).count()
            == 0
        )

    @property
    def website_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.WEBSITE)

    @property
    def compliance_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.COMPLIANCE)

    @property
    def non_accessible_statement_check_results(self):
        return self.statement_check_results.filter(
            type=StatementCheck.Type.NON_ACCESSIBLE
        )

    @property
    def preparation_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.PREPARATION)

    @property
    def feedback_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.FEEDBACK)

    @property
    def custom_statement_check_results(self):
        return self.statement_check_results.filter(type=StatementCheck.Type.CUSTOM)


class RetestPage(models.Model):
    """
    Model for equality body requested retest page
    """

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    page = models.ForeignKey(Page, on_delete=models.PROTECT)
    missing_date = models.DateField(null=True, blank=True)
    additional_issues_notes = models.TextField(default="", blank=True)
    complete_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return f"{self.page}"

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-retest-page-checks", kwargs={"pk": self.pk})

    @property
    def heading(self):
        return f"{self.retest} | {self.page}"

    @property
    def all_check_results(self):
        return self.retestcheckresult_set.all()

    @property
    def unfixed_check_results(self):
        return self.all_check_results.exclude(
            retest_state=CheckResult.RetestResult.FIXED
        )

    @property
    def original_check_results(self):
        return self.retest.original_retest.retestpage_set.get(
            page=self.page
        ).all_check_results

    @property
    def all_retest_pages(self):
        """Return all retest pages for this page"""
        return RetestPage.objects.filter(page=self.page)


class RetestCheckResult(models.Model):
    """
    Model for equality body requested retest result
    """

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=0, blank=True)
    issue_identifier = models.CharField(max_length=20, default="")
    retest_page = models.ForeignKey(RetestPage, on_delete=models.PROTECT)
    check_result = models.ForeignKey(CheckResult, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    retest_state = models.CharField(
        max_length=20,
        choices=CheckResult.RetestResult.choices,
        default=CheckResult.RetestResult.NOT_RETESTED,
    )
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    @property
    def matching_wcag_retest_check_results(self) -> dict[str, str]:
        """Other retest check results with retest notes for same WCAGDefinition"""
        return (
            self.retest.check_results.filter(
                check_result__wcag_definition=self.check_result.wcag_definition
            )
            .exclude(retest_page=self.retest_page)
            .exclude(retest_notes="")
        )

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(
                fields=[
                    "issue_identifier",
                ]
            ),
        ]

    def __str__(self) -> str:
        return f"{self.retest_page} | {self.check_result}"

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        if not self.id:
            if self.id_within_case == 0:
                self.id_within_case = self.check_result.id_within_case
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.retest.simplified_case, issue=self
            )
        super().save(*args, **kwargs)

    @property
    def wcag_definition(self):
        return self.check_result.wcag_definition

    @property
    def original_retest_check_result(self):
        """Return original copy of 12-week retest result for this check"""
        return self.retest.original_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def latest_retest_check_result(self):
        """Return latest retest result for this check"""
        return self.retest.latest_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def previous_retest_check_result(self):
        """Return previous retest result for this check"""
        return self.retest.previous_retest.retestcheckresult_set.filter(
            check_result=self.check_result
        ).first()

    @property
    def all_retest_check_results(self):
        """Return all retest results for this check"""
        return RetestCheckResult.objects.filter(check_result=self.check_result)


class RetestStatementCheckResult(models.Model):
    """
    Model for accessibility statement-specific check result
    """

    class Result(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        NOT_TESTED = "not-tested", "Not tested"

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=0, blank=True)
    issue_identifier = models.CharField(max_length=20, default="")
    statement_check = models.ForeignKey(
        StatementCheck, on_delete=models.PROTECT, null=True, blank=True
    )
    type = models.CharField(
        max_length=20,
        choices=StatementCheck.Type.choices,
        default=StatementCheck.Type.CUSTOM,
    )
    check_result_state = models.CharField(
        max_length=10,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    comment = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["statement_check__position", "id"]
        indexes = [
            models.Index(
                fields=[
                    "issue_identifier",
                ]
            ),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.id:
            if self.id_within_case == 0:
                self.id_within_case = (
                    RetestStatementCheckResult.objects.filter(
                        retest__simplified_case=self.retest.simplified_case
                    ).aggregate(Max("id_within_case", default=0))["id_within_case__max"]
                    + 1
                )
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.retest.simplified_case,
                issue=self,
                custom_issue=self.statement_check is None,
            )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.statement_check is None:
            return f"{self.retest} | Custom [{self.issue_identifier}]"
        return f"{self.retest} | {self.statement_check} [{self.issue_identifier}]"

    @property
    def label(self):
        return self.statement_check.label if self.statement_check else "Custom"


class StatementPage(models.Model):
    """
    Model to store links to statement pages found at various stages in the life
    of a case.
    """

    class AddedStage(models.TextChoices):
        INITIAL = "initial", "Initial"
        TWELVE_WEEK = "12-week-retest", "12-week retest"
        RETEST = "retest", "Equality body retest"

    audit = models.ForeignKey(Audit, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)

    url = models.TextField(default="", blank=True)
    backup_url = models.TextField(default="", blank=True)
    added_stage = models.CharField(
        max_length=20, choices=AddedStage.choices, default=AddedStage.INITIAL
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:  # pylint: disable=invalid-str-returned
        return self.url or self.backup_url
