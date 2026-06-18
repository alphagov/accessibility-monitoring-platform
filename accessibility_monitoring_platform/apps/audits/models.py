"""
Models - audits (called tests by the users)
"""

from __future__ import annotations

from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Case as DjangoCase
from django.db.models import Q, When
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from ..common.models import Boolean, StartEndDateManager, VersionModel
from ..common.utils import amp_format_date, calculate_percentage
from ..simplified.models import CaseCompliance, SimplifiedCase

ISSUE_IDENTIFIER_WCAG: str = "A"
ISSUE_IDENTIFIER_STATEMENT: str = "S"


def build_issue_identifier(
    simplified_case: SimplifiedCase,
    issue: WcagCheckResultInitial | StatementCheckResultRound,
    custom_issue: bool = False,
    id_within_case: int = 1,
) -> str:
    """Format and return issue identifier"""
    issue_type: str = (
        ISSUE_IDENTIFIER_WCAG
        if isinstance(issue, WcagCheckResultInitial)
        else ISSUE_IDENTIFIER_STATEMENT
    )
    if custom_issue:
        issue_type += "C"
    return f"{simplified_case.case_number}-{issue_type}-{id_within_case}"


class Audit(VersionModel):
    """Model for test"""

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
    screen_size = models.CharField(  # KEEP
        max_length=20,
        choices=ScreenSize.choices,
        default=ScreenSize.SIZE_13,
    )
    exemptions_state = models.CharField(  # KEEP
        max_length=20,
        choices=Exemptions.choices,
        default=Exemptions.UNKNOWN,
    )
    exemptions_notes = models.TextField(default="", blank=True)  # KEEP
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

    # Statement links
    audit_statement_pages_complete_date = models.DateField(null=True, blank=True)

    # Statement backups
    audit_initial_statement_backup_complete_date = models.DateField(
        null=True, blank=True
    )

    # Statement checking overview
    statement_extra_report_text = models.TextField(default="", blank=True)  # KEEP
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

    # Statement checking disporportionate burden
    audit_statement_disproportionate_complete_date = models.DateField(
        null=True, blank=True
    )

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

    # Statement backups
    audit_retest_statement_backup_complete_date = models.DateField(
        null=True, blank=True
    )

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

    # Retest statement checking feedback
    audit_retest_statement_disproportionate_complete_date = models.DateField(
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
        return f"{self.simplified_case} (Test {amp_format_date(self.date_of_test)})"


class AuditOverview(models.Model):

    simplified_case = models.OneToOneField(
        SimplifiedCase,
        on_delete=models.PROTECT,
        related_name="auditoverview_simplifiedcase",
        blank=True,
        null=True,
    )
    published_report_data_updated_time = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        if self.id is None:
            self.updated = timezone.now()
        super().save(*args, **kwargs)

    @property
    def wcag_audits(self) -> QuerySet[WcagAudit]:
        return self.simplified_case.wcagaudit_set.filter(is_deleted=False)

    @property
    def wcag_audit_initial(self) -> WcagAudit | None:
        return self.wcag_audits.filter(
            audit_round_type=WcagAudit.AuditRoundType.INITIAL
        ).first()

    @property
    def first_wcag_audit_12_week_retest(self) -> WcagAudit | None:
        return self.wcag_audits.filter(
            audit_round_type=WcagAudit.AuditRoundType.TWELVE_WEEK
        ).first()

    @property
    def equality_body_wcag_audits(self) -> WcagAudit | None:
        return self.wcag_audits.filter(
            audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY
        )

    @property
    def first_wcag_audit_equality_body_retest(self) -> WcagAudit | None:
        return self.equality_body_wcag_audits.first()

    @property
    def last_equality_body_wcag_audit(self) -> WcagAudit | None:
        return self.equality_body_wcag_audits.last()

    @property
    def website_compliance_display(self) -> str:
        if (
            self.first_wcag_audit_12_week_retest is not None
            and self.first_wcag_audit_12_week_retest.compliance_state
            != WcagAudit.WebsiteCompliance.UNKNOWN
        ):
            return self.first_wcag_audit_12_week_retest.get_compliance_state_display()
        return self.wcag_audit_initial.get_compliance_state_display()

    @property
    def statement_pages(self) -> QuerySet[StatementPage]:
        return self.statementpage_set.filter(is_deleted=False)

    @property
    def latest_statement_link(self) -> str | None:
        for statement_page in self.statement_pages.order_by("-id"):
            if statement_page.url:
                return statement_page.url

    @property
    def archived_google_drive_links(self) -> QuerySet[StatementPage]:
        """Return statement pages with google drive backup urls"""
        return self.statement_pages.filter(backup_url__contains="drive.google.com")

    @property
    def unique_statement_page_urls(self) -> list[StatementPage]:
        """Return the first statement page for each URL"""
        statement_urls: list[str] = []
        unique_url_statement_pages: list[StatementPage] = []
        for statement_page in self.statement_pages.exclude(url=""):
            if statement_page.url not in statement_urls:
                statement_urls.append(statement_page.url)
                unique_url_statement_pages.append(statement_page)
        return unique_url_statement_pages

    @property
    def accessibility_statement_found(self) -> bool:
        return self.statement_pages.count() > 0 and self.latest_statement_link != ""

    @property
    def statement_audits(self) -> QuerySet[StatementAudit]:
        return self.simplified_case.statementaudit_set.filter(is_deleted=False)

    @property
    def statement_audit_initial(self) -> StatementAudit | None:
        return self.statement_audits.filter(
            audit_round_type=StatementAudit.AuditRoundType.INITIAL
        ).first()

    @property
    def twelve_week_statement_audits(self) -> StatementAudit | None:
        return self.statement_audits.filter(
            audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK
        )

    @property
    def equality_body_statement_audits(self) -> StatementAudit | None:
        return self.statement_audits.filter(
            audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY
        )

    @property
    def first_statement_audit_12_week_retest(self) -> StatementAudit | None:
        if self.twelve_week_statement_audits is not None:
            return self.twelve_week_statement_audits.first()

    @property
    def last_equality_body_statement_audit(self) -> WcagAudit | None:
        if self.equality_body_statement_audits is not None:
            return self.equality_body_statement_audits.last()

    @property
    def all_overview_statement_checks_have_passed(self) -> bool:
        """Check all overview statement checks have passed test or retest"""
        if (
            self.statement_audit_initial is None
            or self.statement_audit_initial.overview_statement_check_results.count()
            == 0
        ):
            return False
        if self.first_statement_audit_12_week_retest is None:
            return (
                self.statement_audit_initial.overview_statement_check_results.exclude(
                    check_result_state=StatementCheckResultRound.Result.YES
                ).count()
                == 0
            )
        return (
            self.statement_audit_initial.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResultRound.Result.YES
            ).count()
            == 0
            or self.first_statement_audit_12_week_retest.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResult.ResultRetest.YES
            ).count()
            == 0
        )


class AuditRound(VersionModel):
    """Model for round of testing"""

    class AuditRoundType(models.TextChoices):
        INITIAL = "initial", "Initial test"
        TWELVE_WEEK = "12-week", "12-week retest"
        EQUALITY_BODY = "equality-body", "Equality body retest"

    simplified_case = models.ForeignKey(
        SimplifiedCase,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    audit_round_type = models.CharField(
        max_length=20,
        choices=AuditRoundType.choices,
        default=AuditRoundType.INITIAL,
    )
    round_number = models.IntegerField(default=0, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    date_of_test = models.DateField(default=date.today)
    notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["id"]

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.simplified_case} {self.get_audit_round_type_display()}{self.round_suffix} ({amp_format_date(self.date_of_test)})"

    @property
    def round_suffix(self) -> str:
        if (
            self.audit_round_type == WcagAudit.AuditRoundType.INITIAL
            or self.audit_round_type == WcagAudit.AuditRoundType.TWELVE_WEEK
        ):
            round_suffix: str = ""
        else:
            round_number: int = self.round_number - 1
            round_suffix: str = f" #{round_number}"
        return round_suffix

    def short_name(self) -> str:
        return f"{self.get_audit_round_type_display()}{self.round_suffix}"

    def short_name_with_date_of_test(self) -> str:
        return f"{self.get_audit_round_type_display()}{self.round_suffix} ({amp_format_date(self.date_of_test)})"


class WcagAudit(AuditRound):
    """Model for testing WCAG"""

    class ScreenSize(models.TextChoices):
        SIZE_13 = "13in", "13 inch"
        SIZE_14 = "14in", "14 inch"
        SIZE_15 = "15in", "15 inch"

    class Exemptions(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        UNKNOWN = "unknown", "Unknown"

    class WebsiteCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Fully compliant"
        PARTIALLY = "partially-compliant", "Partially compliant"
        UNKNOWN = "not-known", "Not known"

    # metadata page
    # date_of_test
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
    metadata_complete_date = models.DateField(null=True, blank=True)

    # Pages page
    pages_complete_date = models.DateField(null=True, blank=True)

    # Retest comparison page
    comparison_complete_date = models.DateField(null=True, blank=True)

    # Website decision
    compliance_state = models.CharField(
        max_length=20,
        choices=WebsiteCompliance.choices,
        default=WebsiteCompliance.UNKNOWN,
    )
    compliance_notes = models.TextField(default="", blank=True)
    compliance_decision_complete_date = models.DateField(null=True, blank=True)

    # WCAG Summary
    summary_complete_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        if self.id is None:
            self.round_number = self.simplified_case.wcagaudit_set.all().count()
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-audit-metadata", kwargs={"pk": self.pk})

    @property
    def equivalent_statement_audit(self) -> StatementAudit:
        """Return matching statement audit"""
        return StatementAudit.objects.get(
            simplified_case=self.simplified_case,
            round_number=self.round_number,
        )

    @property
    def previous_equality_body_retest(self) -> WcagAudit | None:
        """Return previous equality body or 12-week retest"""
        if self.audit_round_type != WcagAudit.AuditRoundType.EQUALITY_BODY:
            return None
        return WcagAudit.objects.filter(
            simplified_case=self.simplified_case,
            round_number=self.round_number - 1,
        ).first()

    @property
    def equivalent_equality_body_statement_retest(self) -> StatementAudit | None:
        """Return matching equality body statement retest"""
        return StatementAudit.objects.filter(
            simplified_case=self.simplified_case,
            audit_round_type=StatementAudit.AuditRoundType.EQUALITY_BODY,
            round_number=self.round_number,
        ).first()

    @property
    def equality_body_retest_name(self) -> str:
        retest_number: int = self.round_number - 1
        return f"Retest #{retest_number}"

    @property
    def every_wcag_page_initials(self) -> QuerySet[WcagPageInitial]:
        """Sort page of type PDF to be last apart from the accessibility statement"""
        return (
            self.wcagpageinitial_set.filter(is_deleted=False)
            .annotate(
                position_pdfs_statements_last=DjangoCase(
                    When(page_type=WcagPageInitial.Type.PDF, then=1),
                    When(page_type=WcagPageInitial.Type.STATEMENT, then=2),
                    default=0,
                )
            )
            .order_by("position_pdfs_statements_last", "id")
        )

    @property
    def accessibility_statement_wcag_page_initial(self) -> WcagPageInitial | None:
        return self.every_wcag_page_initials.filter(
            page_type=Page.Type.STATEMENT
        ).first()

    @property
    def testable_wcag_page_initials(self) -> QuerySet[WcagPageInitial]:
        return self.every_wcag_page_initials.exclude(not_found=Boolean.YES).exclude(
            url=""
        )

    @property
    def wcag_page_retests(self) -> QuerySet[WcagPageRetest]:
        return self.wcagpageretest_set.filter(is_deleted=False).exclude(
            wcag_page_initial__url=""
        )

    @property
    def retestable_wcag_page_retests(self):
        return self.wcag_page_retests.filter(page_missing_date=None)

    @property
    def wcag_page_retests_missing_at_retest(self):
        return self.wcag_page_retests.exclude(page_missing_date=None)

    @property
    def standard_wcag_page_initials(self) -> QuerySet[WcagPageInitial]:
        return self.every_wcag_page_initials.exclude(
            page_type=WcagPageInitial.Type.EXTRA
        )

    @property
    def html_wcag_page_initials(self) -> QuerySet[WcagPageInitial]:
        return self.every_wcag_page_initials.exclude(page_type=WcagPageInitial.Type.PDF)

    @property
    def extra_wcag_page_initials(self) -> QuerySet[WcagPageInitial]:
        return self.html_wcag_page_initials.filter(page_type=WcagPageInitial.Type.EXTRA)

    @property
    def wcag_failed_check_result_initials(self) -> QuerySet[WcagCheckResultInitial]:
        return (
            self.wcagcheckresultinitial_set.filter(
                is_deleted=False,
                check_result_state=WcagCheckResultInitial.Result.ERROR,
                wcag_page_initial__is_deleted=False,
                wcag_page_initial__not_found=Boolean.NO,
                wcag_page_initial__is_contact_page=Boolean.NO,
            )
            .annotate(
                position_pdf_and_statement_page_last=DjangoCase(
                    When(wcag_page_initial__page_type=WcagPageInitial.Type.PDF, then=1),
                    When(
                        wcag_page_initial__page_type=WcagPageInitial.Type.STATEMENT,
                        then=2,
                    ),
                    default=0,
                )
            )
            .order_by(
                "position_pdf_and_statement_page_last",
                "wcag_page_initial__id",
                "wcag_definition__id",
            )
            .select_related("wcag_page_initial", "wcag_definition")
            .all()
        )

    @property
    def wcag_failed_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return (
            self.wcagcheckresultretest_set.filter(
                is_deleted=False,
                wcag_check_result_initial__check_result_state=WcagCheckResultInitial.Result.ERROR,
                wcag_check_result_initial__wcag_page_initial__is_deleted=False,
                wcag_check_result_initial__wcag_page_initial__not_found=Boolean.NO,
                wcag_check_result_initial__wcag_page_initial__is_contact_page=Boolean.NO,
                wcag_page_retest__page_missing_date=None,
            )
            .annotate(
                position_pdf_and_statement_page_last=DjangoCase(
                    When(
                        wcag_page_retest__wcag_page_initial__page_type=WcagPageInitial.Type.PDF,
                        then=1,
                    ),
                    When(
                        wcag_page_retest__wcag_page_initial__page_type=WcagPageInitial.Type.STATEMENT,
                        then=2,
                    ),
                    default=0,
                )
            )
            .order_by(
                "position_pdf_and_statement_page_last",
                "wcag_page_retest__id",
                "wcag_check_result_initial__wcag_definition__id",
            )
            .select_related(
                "wcag_page_retest__wcag_page_initial",
                "wcag_check_result_initial__wcag_definition",
            )
            .all()
        )

    @property
    def wcag_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return self.wcagcheckresultretest_set.filter(
            is_deleted=False,
            wcag_check_result_initial__wcag_page_initial__not_found=Boolean.NO,
        )

    @property
    def wcag_fixed_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return self.wcag_check_result_retests.filter(
            retest_state=WcagCheckResultRetest.RetestResult.FIXED,
        )

    @property
    def wcag_unfixed_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return self.wcag_check_result_retests.filter(
            wcag_check_result_initial__check_result_state=WcagCheckResultInitial.Result.ERROR
        ).exclude(
            retest_state=WcagCheckResultRetest.RetestResult.FIXED,
        )

    @property
    def percentage_wcag_issues_fixed(self) -> int:
        return calculate_percentage(
            total=self.simplified_case.audit_overview.wcag_audit_initial.wcag_failed_check_result_initials.count(),
            partial=self.wcag_fixed_check_result_retests.count(),
        )

    @property
    def missing_wcag_page_retests(self) -> QuerySet[WcagPageRetest]:
        return self.wcagpageretest_set.filter(is_deleted=False).exclude(
            page_missing_date=None
        )

    @property
    def missing_at_retest_check_results(self):
        return self.wcagcheckresultretest_set.filter(
            is_deleted=False,
            wcag_page_retest__in=self.missing_wcag_page_retests,
        )


class StatementAudit(AuditRound):
    """Model for testing accessibility statement content"""

    class DisproportionateBurden(models.TextChoices):
        NO_ASSESSMENT = "no-assessment", "Claim with no assessment"
        ASSESSMENT = "assessment", "Claim with assessment"
        NO_CLAIM = "no-claim", "No claim"
        NO_STATEMENT = "no-statement", "No statement"
        NOT_CHECKED = "not-checked", "Not checked"

    class StatementCompliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        NOT_COMPLIANT = "not-compliant", "Not compliant or no statement"
        UNKNOWN = "unknown", "Not assessed"

    # Statement links
    pages_complete_date = models.DateField(null=True, blank=True)

    # Statement backups
    backup_complete_date = models.DateField(null=True, blank=True)

    # Statement checking overview
    statement_extra_report_text = models.TextField(default="", blank=True)  # KEEP
    statement_overview_complete_date = models.DateField(null=True, blank=True)

    # Statement checking website
    statement_website_complete_date = models.DateField(null=True, blank=True)

    # Statement checking compliance
    statement_compliance_complete_date = models.DateField(null=True, blank=True)

    # Statement checking non-accessible content
    statement_non_accessible_complete_date = models.DateField(null=True, blank=True)

    # Statement checking preparation
    statement_preparation_complete_date = models.DateField(null=True, blank=True)

    # Statement checking feedback
    statement_feedback_complete_date = models.DateField(null=True, blank=True)

    # Statement checking disporportionate burden
    statement_disproportionate_complete_date = models.DateField(null=True, blank=True)

    # Statement checking other
    statement_custom_complete_date = models.DateField(null=True, blank=True)

    # Initial disproportionate burden claim
    disproportionate_burden_claim = models.CharField(
        max_length=20,
        choices=DisproportionateBurden.choices,
        default=DisproportionateBurden.NOT_CHECKED,
    )
    disproportionate_burden_notes = models.TextField(default="", blank=True)
    disproportionate_burden_complete_date = models.DateField(null=True, blank=True)

    # Statement decision
    compliance_state = models.CharField(
        max_length=200,
        choices=StatementCompliance.choices,
        default=StatementCompliance.UNKNOWN,
    )
    compliance_notes = models.TextField(default="", blank=True)
    compliance_complete_date = models.DateField(null=True, blank=True)

    # Statement Summary
    summary_complete_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        if self.id is None:
            self.round_number = self.simplified_case.statementaudit_set.all().count()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.audit_round_type == WcagAudit.AuditRoundType.INITIAL:
            round_suffix: str = ""
        else:
            round_suffix: str = f" #{self.round_number}"
        return f"{self.simplified_case} {self.get_audit_round_type_display()}{round_suffix} ({amp_format_date(self.date_of_test)})"

    @property
    def previous_equality_body_retest(self):
        """Return previous equality body retest"""
        return StatementAudit.objects.filter(
            simplified_case=self.simplified_case,
            audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
            round_number=self.round_number - 1,
        ).first()

    @property
    def equivalent_equality_body_wcag_retest(self) -> WcagAudit | None:
        """Return matching equality body wcag retest"""
        return WcagAudit.objects.filter(
            simplified_case=self.simplified_case,
            audit_round_type=WcagAudit.AuditRoundType.EQUALITY_BODY,
            round_number=self.round_number,
        ).first()

    @property
    def statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.statementcheckresultround_set.exclude(is_deleted=True)

    @property
    def overview_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.OVERVIEW)

    @property
    def statement_found_check(self) -> StatementCheckResultRound | None:
        return self.overview_statement_check_results.first()

    @property
    def statement_structure_check(self):
        """Only worked prior to 30 July 2025 when there was a second overview check"""
        return self.overview_statement_check_results.last()

    @property
    def website_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.WEBSITE)

    @property
    def compliance_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.COMPLIANCE)

    @property
    def non_accessible_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(
            type=StatementCheck.Type.NON_ACCESSIBLE
        )

    @property
    def preparation_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.PREPARATION)

    @property
    def feedback_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.FEEDBACK)

    @property
    def custom_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.CUSTOM)

    @property
    def new_12_week_custom_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(type=StatementCheck.Type.RETEST)

    @property
    def failed_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(
            check_result_state=StatementCheckResult.Result.NO
        )

    @property
    def passed_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(
            check_result_state=StatementCheckResultRound.Result.YES
        )

    @property
    def fixed_statement_check_results(self) -> QuerySet[StatementCheckResultRound]:
        return self.failed_statement_check_results.filter(
            statementcheckresultround__check_result_state=StatementCheckResult.Result.YES
        )

    @property
    def outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.statement_check_results.filter(
            Q(check_result_state=StatementCheckResult.Result.NO)
            | Q(check_result_state=StatementCheckResult.Result.NOT_TESTED)
        )

    @property
    def overview_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.OVERVIEW
        )

    @property
    def website_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.WEBSITE
        )

    @property
    def compliance_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.COMPLIANCE
        )

    @property
    def non_accessible_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.NON_ACCESSIBLE
        )

    @property
    def preparation_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.PREPARATION
        )

    @property
    def feedback_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.FEEDBACK
        )

    @property
    def disproportionate_outstanding_statement_check_results(
        self,
    ) -> QuerySet[StatementCheckResultRound]:
        return self.outstanding_statement_check_results.filter(
            type=StatementCheck.Type.DISPROPORTIONATE
        )

    @property
    def overview_statement_checks_complete(self) -> bool:
        return (
            self.overview_statement_check_results.filter(
                check_result_state=StatementCheckResult.Result.NOT_TESTED
            ).count()
            == 0
        )

    @property
    def all_overview_statement_checks_have_passed(self) -> bool:
        """Check all overview statement checks have passed"""
        if self.overview_statement_check_results.count() == 0:
            return False
        return (
            self.overview_statement_check_results.exclude(
                check_result_state=StatementCheckResult.Result.YES
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
    def latest_statement_link(self) -> str | None:
        for statement_page in self.simplified_case.statement_pages.order_by("-id"):
            if statement_page.url:
                return statement_page.url


class Page(models.Model):

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


class WcagPageInitial(models.Model):

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

    wcag_audit = models.ForeignKey(WcagAudit, on_delete=models.PROTECT, null=True)
    page_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.EXTRA
    )
    name = models.TextField(default="", blank=True)
    url = models.TextField(default="", blank=True)
    location = models.TextField(default="", blank=True)
    not_found = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    is_contact_page = models.CharField(
        max_length=20, choices=Boolean.choices, default=Boolean.NO
    )
    notes = models.TextField(default="", blank=True)
    no_errors_date = models.DateField(null=True, blank=True)
    complete_date = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name if self.name else self.get_page_type_display()

    def get_absolute_url(self) -> str:
        return reverse("audits:edit-audit-page-checks", kwargs={"pk": self.pk})

    @property
    def page_title(self) -> str:
        title: str = str(self)
        if self.page_type != WcagPageInitial.Type.PDF:
            title += " page"
        return title

    @property
    def all_wcag_check_result_initials(self) -> QuerySet[WcagCheckResultInitial]:
        return (
            self.wcagcheckresultinitial_set.filter(is_deleted=False)
            .order_by("wcag_definition__id")
            .select_related("wcag_definition")
            .all()
        )

    @property
    def failed_wcag_check_result_initials(self) -> QuerySet[WcagCheckResultInitial]:
        return self.all_wcag_check_result_initials.filter(
            check_result_state=WcagCheckResultInitial.Result.ERROR
        )

    @property
    def count_failed_wcag_check_result_initials(self) -> int:
        return self.failed_wcag_check_result_initials.count()

    @property
    def unfixed_wcag_check_result_initials(self) -> QuerySet[WcagCheckResultInitial]:
        return self.failed_wcag_check_result_initials.exclude(
            wcagcheckresultretest__retest_state=WcagCheckResultRetest.RetestResult.FIXED
        )

    @property
    def wcag_check_result_initials_by_wcag_definition(
        self,
    ) -> dict[WcagDefinition, WcagCheckResultInitial]:
        wcag_check_result_initials: QuerySet[WcagCheckResultInitial] = (
            self.all_wcag_check_result_initials
        )
        return {
            wcag_check_result_initial.wcag_definition: wcag_check_result_initial
            for wcag_check_result_initial in wcag_check_result_initials
        }

    @property
    def anchor(self) -> str:
        return f"test-page-{self.id}"


class WcagPageRetest(models.Model):
    wcag_audit = models.ForeignKey(WcagAudit, on_delete=models.PROTECT, null=True)
    wcag_page_initial = models.ForeignKey(WcagPageInitial, on_delete=models.PROTECT)
    complete_date = models.DateField(null=True, blank=True)
    url = models.TextField(default="", blank=True)
    location = models.TextField(default="", blank=True)
    no_errors_date = models.DateField(null=True, blank=True)
    page_missing_date = models.DateField(null=True, blank=True)
    notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return str(self.wcag_page_initial)

    @property
    def page_title(self) -> str:
        return self.wcag_page_initial.page_title

    @property
    def all_wcag_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return (
            self.wcagcheckresultretest_set.filter(
                is_deleted=False, wcag_audit=self.wcag_audit
            )
            .order_by("wcag_check_result_initial__wcag_definition__id")
            .select_related("wcag_check_result_initial__wcag_definition")
            .all()
        )

    @property
    def failed_wcag_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return self.all_wcag_check_result_retests.filter(
            retest_state=WcagCheckResultRetest.RetestResult.NOT_FIXED
        )

    @property
    def unfixed_wcag_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        return self.all_wcag_check_result_retests.exclude(
            retest_state=WcagCheckResultRetest.RetestResult.FIXED
        )

    @property
    def check_results_by_wcag_definition(self):
        check_results: QuerySet[CheckResult] = self.all_wcag_check_result_retests
        return {
            check_result.wcag_definition: check_result for check_result in check_results
        }

    @property
    def all_wcag_page_retests(self):
        """Return all wcag page retests for this page"""
        return WcagPageRetest.objects.filter(wcag_page_initial=self.wcag_page_initial)

    @property
    def latest_page_url(self):
        """Return most recent URL entered for this page"""
        url: str = self.wcag_page_initial.url
        for wcag_page_retest in self.all_wcag_page_retests:
            if wcag_page_retest.url:
                url = wcag_page_retest.url
        return url

    @property
    def latest_page_location(self):
        """Return most recent location entered for this page"""
        location: str = self.wcag_page_initial.location
        for wcag_page_retest in self.all_wcag_page_retests:
            if wcag_page_retest.location:
                location = wcag_page_retest.location
        return location


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


class WcagCheckResultInitial(models.Model):

    class Result(models.TextChoices):
        ERROR = "error", "Error found"
        NO_ERROR = "no-error", "No issue"
        NOT_TESTED = "not-tested", "Not tested"

    wcag_audit = models.ForeignKey(WcagAudit, on_delete=models.PROTECT, null=True)
    wcag_page_initial = models.ForeignKey(WcagPageInitial, on_delete=models.PROTECT)
    issue_identifier = models.CharField(max_length=20, default="")
    type = models.CharField(
        max_length=20,
        choices=WcagDefinition.Type.choices,
        default=WcagDefinition.Type.PDF,
    )
    wcag_definition = models.ForeignKey(
        WcagDefinition,
        on_delete=models.PROTECT,
    )
    check_result_state = models.CharField(
        max_length=20,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        if not self.id and not self.issue_identifier:
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.wcag_audit.simplified_case,
                issue=self,
                id_within_case=self.wcag_audit.wcagcheckresultinitial_set.all().count()
                + 1,
            )
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.issue_identifier} ({self.wcag_page_initial})"

    @property
    def twelve_week_retest(self) -> WcagCheckResultRetest | None:
        return WcagCheckResultRetest.objects.filter(
            wcag_check_result_initial=self
        ).first()

    @property
    def matching_wcag_with_notes_check_results(self) -> dict[str, str]:
        """Other check results with notes for matching WcagDefinition"""
        return (
            self.wcag_audit.wcag_failed_check_result_initials.filter(
                wcag_definition=self.wcag_definition
            )
            .exclude(wcag_page_initial=self.wcag_page_initial)
            .exclude(notes="")
        )


class WcagCheckResultRetest(models.Model):

    class RetestResult(models.TextChoices):
        FIXED = "fixed", "Fixed"
        NOT_FIXED = "not-fixed", "Not fixed"
        NOT_RETESTED = "not-retested", "Not retested"

    wcag_audit = models.ForeignKey(WcagAudit, on_delete=models.PROTECT, null=True)
    wcag_page_retest = models.ForeignKey(WcagPageRetest, on_delete=models.PROTECT)
    wcag_check_result_initial = models.ForeignKey(
        WcagCheckResultInitial, on_delete=models.PROTECT
    )
    wcag_definition = models.ForeignKey(
        WcagDefinition,
        on_delete=models.PROTECT,
    )
    retest_state = models.CharField(
        max_length=20,
        choices=RetestResult.choices,
        default=RetestResult.NOT_RETESTED,
    )
    notes = models.TextField(default="", blank=True)
    is_deleted = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        self.updated = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.wcag_check_result_initial.issue_identifier

    @property
    def other_wcag_check_result_retests(self) -> QuerySet[WcagCheckResultRetest]:
        """Other check results for matching WcagDefinition"""
        return WcagCheckResultRetest.objects.filter(
            wcag_check_result_initial=self.wcag_check_result_initial
        ).exclude(wcag_page_retest=self.wcag_page_retest)

    @property
    def previous_wcag_check_result_retest(self) -> WcagCheckResultRetest | None:
        """Other check results for matching WcagDefinition"""
        if (
            self.wcag_audit
            == self.wcag_audit.simplified_case.audit_overview.first_wcag_audit_equality_body_retest
        ):
            return WcagCheckResultRetest.objects.filter(
                wcag_check_result_initial=self.wcag_check_result_initial,
                wcag_audit=self.wcag_audit.simplified_case.audit_overview.first_wcag_audit_12_week_retest,
            ).first()
        return WcagCheckResultRetest.objects.filter(
            wcag_check_result_initial=self.wcag_check_result_initial,
            wcag_audit=self.wcag_audit.previous_equality_body_retest,
        ).first()


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


class WcagCheckResultInitialNotesHistory(models.Model):
    """Model to record history of changes to WcagCheckResultInitial notes"""

    wcag_check_result_initial = models.ForeignKey(
        WcagCheckResultInitial, on_delete=models.PROTECT
    )
    notes = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.wcag_check_result_initial} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "WCAG check result initial notes histories"


class WcagCheckResultRetestNotesHistory(models.Model):
    """Model to record history of changes to WcagCheckResultRetest notes"""

    wcag_check_result_retest = models.ForeignKey(
        WcagCheckResultRetest, on_delete=models.PROTECT
    )
    retest_state = models.CharField(
        max_length=20,
        choices=WcagCheckResultRetest.RetestResult.choices,
        default=WcagCheckResultRetest.RetestResult.NOT_RETESTED,
    )
    notes = models.TextField(default="", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.wcag_check_result_retest} {self.created} {self.created_by}"

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "WCAG check result retest notes histories"


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
        RETEST = "retest-custom", "Retest custom statement issues"
        DISPROPORTIONATE = "disproportionate", "Disproportionate burden"

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


class StatementCheckResultRound(models.Model):

    class Result(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        NOT_TESTED = "not-tested", "Not tested"

    statement_audit = models.ForeignKey(StatementAudit, on_delete=models.PROTECT)
    statement_check = models.ForeignKey(
        StatementCheck, on_delete=models.PROTECT, null=True, blank=True
    )
    statement_check_result_initial = models.ForeignKey(
        "StatementCheckResultRound", on_delete=models.PROTECT, blank=True, null=True
    )
    type = models.CharField(
        max_length=20,
        choices=StatementCheck.Type.choices,
        default=StatementCheck.Type.CUSTOM,
    )
    issue_identifier = models.CharField(max_length=20, default="")
    check_result_state = models.CharField(
        max_length=10,
        choices=Result.choices,
        default=Result.NOT_TESTED,
    )
    public_comment = models.TextField(default="", blank=True)
    auditor_information = models.TextField(default="", blank=True)
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
            return f"{self.statement_audit} | Custom [{self.issue_identifier}]"
        return (
            f"{self.statement_audit} | {self.statement_check} [{self.issue_identifier}]"
        )

    def save(self, *args, **kwargs) -> None:
        if not self.id and not self.issue_identifier:
            if self.statement_check:
                id_within_case: int = self.statement_check.issue_number
            else:
                id_within_case: int = (
                    self.statement_audit.statementcheckresultround_set.filter(
                        statement_check=None
                    ).count()
                    + 1
                )
            self.issue_identifier = build_issue_identifier(
                simplified_case=self.statement_audit.simplified_case,
                issue=self,
                custom_issue=self.statement_check is None,
                id_within_case=id_within_case,
            )
        if not self.id and self.statement_check is None:
            self.check_result_state = StatementCheckResultRound.Result.NO
        super().save(*args, **kwargs)

    @property
    def label(self):
        return self.statement_check.label if self.statement_check else "Custom"

    @property
    def display_value(self):
        value_str: str = self.get_check_result_state_display()
        if self.public_comment:
            value_str += f"<br><br>Auditor's comment: {self.public_comment}"
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

    @property
    def twelve_week_retest(self) -> StatementCheckResult | None:
        return (
            StatementCheckResultRound.objects.filter(
                is_deleted=False,
                statement_audit__simplified_case=self.statement_audit.simplified_case,
                statement_audit__audit_round_type=StatementAudit.AuditRoundType.TWELVE_WEEK,
                statement_check=self.statement_check,
            )
            .exclude(statement_check=None)
            .first()
        )


class Retest(VersionModel):
    """
    Model for retest of outstanding issues requested by an equality body
    """

    class Compliance(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        PARTIAL = "partially-compliant", "Partially compliant"
        NOT_KNOWN = "not-known", "Not known"

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
    statement_backup_complete_date = models.DateField(null=True, blank=True)

    statement_overview_complete_date = models.DateField(null=True, blank=True)
    statement_website_complete_date = models.DateField(null=True, blank=True)
    statement_compliance_complete_date = models.DateField(null=True, blank=True)
    statement_non_accessible_complete_date = models.DateField(null=True, blank=True)
    statement_preparation_complete_date = models.DateField(null=True, blank=True)
    statement_feedback_complete_date = models.DateField(null=True, blank=True)
    statement_disproportionate_complete_date = models.DateField(null=True, blank=True)
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
        ordering = ["simplified_case_id", "-id_within_case"]

    def __str__(self) -> str:
        if self.id_within_case == 0:
            return "12-week retest"
        return f"Retest #{self.id_within_case}"


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


class RetestCheckResult(models.Model):
    """
    Model for equality body requested retest result
    """

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    issue_identifier = models.CharField(max_length=20, default="")
    retest_page = models.ForeignKey(RetestPage, on_delete=models.PROTECT)
    id_within_case = models.IntegerField(default=0, blank=True)
    check_result = models.ForeignKey(CheckResult, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    retest_state = models.CharField(
        max_length=20,
        choices=CheckResult.RetestResult.choices,
        default=CheckResult.RetestResult.NOT_RETESTED,
    )
    retest_notes = models.TextField(default="", blank=True)
    updated = models.DateTimeField(null=True, blank=True)

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


class RetestStatementCheckResult(models.Model):
    """
    Model for accessibility statement-specific check result
    """

    class Result(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        NOT_TESTED = "not-tested", "Not tested"

    retest = models.ForeignKey(Retest, on_delete=models.PROTECT)
    statement_audit = models.ForeignKey(
        StatementAudit, on_delete=models.PROTECT, null=True
    )
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

    def __str__(self) -> str:
        if self.statement_check is None:
            return f"{self.statement_audit} | Custom [{self.issue_identifier}]"
        return (
            f"{self.statement_audit} | {self.statement_check} [{self.issue_identifier}]"
        )


class StatementPage(models.Model):
    """
    Model to store links to statement pages found at various stages in the life
    of a case.
    """

    class AddedStage(models.TextChoices):
        ANY = "any", "Any"
        INITIAL = "initial", "Initial"
        TWELVE_WEEK = "12-week-retest", "12-week retest"
        RETEST = "retest", "Equality body retest"

    audit = models.ForeignKey(Audit, on_delete=models.PROTECT, null=True)
    simplified_case = models.ForeignKey(
        SimplifiedCase, on_delete=models.PROTECT, null=True
    )
    audit_overview = models.ForeignKey(
        AuditOverview, on_delete=models.PROTECT, null=True
    )
    is_deleted = models.BooleanField(default=False)

    url = models.TextField(default="", blank=True)
    backup_url = models.TextField(default="", blank=True)
    added_stage = models.CharField(
        max_length=20, choices=AddedStage.choices, default=AddedStage.ANY
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.url or self.backup_url
