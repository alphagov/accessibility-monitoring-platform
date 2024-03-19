"""Models for comment and comment history"""

from typing import List

from django.contrib.auth.models import User
from django.db import models

from ..cases.models import Case, CaseStatus
from ..common.templatetags.common_tags import amp_date


class Export(models.Model):
    """Export model"""

    class ExportStatus(models.TextChoices):
        NOT_EXPORTED = "not", "Not yet exported"
        EXPORTED = "exported", "Exported"

    cutoff_date = models.DateField()
    exporter = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="exporter"
    )
    status = models.CharField(
        max_length=20, choices=ExportStatus, default=ExportStatus.NOT_EXPORTED
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
        return f"Export for {self.cutoff_date:%B %Y}"

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


class ExportCase(models.Model):
    """Model recording which cases are in an export"""

    class ExportStatus(models.TextChoices):
        UNREADY = "unready", "Unready"
        READY = "ready", "Ready"
        EXCLUDED = "excluded", "Excluded"

    export = models.ForeignKey(Export, on_delete=models.PROTECT)
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=ExportStatus, default=ExportStatus.UNREADY
    )
