"""Models for comment and comment history"""

from typing import List

from django.contrib.auth.models import User
from django.db import models

from ..cases.models import Case, CaseStatus
from ..common.utils import amp_format_date


class Export(models.Model):
    """Export model"""

    class Status(models.TextChoices):
        NOT_EXPORTED = "not", "Not yet exported"
        EXPORTED = "exported", "Exported"

    cutoff_date = models.DateField()
    exporter = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="exporter"
    )
    status = models.CharField(
        max_length=20, choices=Status, default=Status.NOT_EXPORTED
    )
    enforcement_body = models.CharField(
        max_length=20,
        choices=Case.EnforcementBody.choices,
        default=Case.EnforcementBody.EHRC,
    )
    export_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering: List[str] = ["-id"]

    def __str__(self) -> str:
        return f"EHRC CSV export {amp_format_date(self.cutoff_date)}"

    def save(self, *args, **kwargs) -> None:
        new_export: bool = not self.id
        super().save(*args, **kwargs)
        if new_export:
            for case_status in CaseStatus.objects.filter(
                status=CaseStatus.Status.CASE_CLOSED_WAITING_TO_SEND
            ).filter(case__compliance_email_sent_date__lte=self.cutoff_date):
                ExportCase.objects.create(
                    export=self,
                    case=case_status.case,
                )

    @property
    def all_cases(self) -> List[Case]:
        return [export_case.case for export_case in self.exportcase_set.all()]

    @property
    def ready_cases(self):
        return [
            export_case.case
            for export_case in self.exportcase_set.filter(
                status=ExportCase.Status.READY
            )
        ]

    @property
    def ready_cases_count(self):
        return self.exportcase_set.filter(status=ExportCase.Status.READY).count()

    @property
    def excluded_cases_count(self):
        return self.exportcase_set.filter(status=ExportCase.Status.EXCLUDED).count()

    @property
    def unready_cases_count(self):
        return self.exportcase_set.filter(status=ExportCase.Status.UNREADY).count()


class ExportCase(models.Model):
    """Model recording which cases are in an export"""

    class Status(models.TextChoices):
        UNREADY = "unready", "Unready"
        READY = "ready", "Ready"
        EXCLUDED = "excluded", "Excluded"

    export = models.ForeignKey(Export, on_delete=models.PROTECT)
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status, default=Status.UNREADY)

    class Meta:
        ordering: List[str] = ["id"]

    def __str__(self) -> str:
        return f"{self.export}: {self.case}"
