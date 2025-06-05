"""Models for comment and comment history"""

from django.contrib.auth.models import User
from django.db import models

from ..cases.models import BaseCase, Case
from ..common.utils import amp_format_date
from .utils import get_exportable_cases


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
        ordering: list[str] = ["-cutoff_date"]

    def __str__(self) -> str:
        return f"{self.enforcement_body.upper()} CSV export {amp_format_date(self.cutoff_date)}"

    def save(self, *args, **kwargs) -> None:
        new_export: bool = not self.id
        super().save(*args, **kwargs)
        if new_export:
            for case in get_exportable_cases(
                cutoff_date=self.cutoff_date, enforcement_body=self.enforcement_body
            ):
                ExportCase.objects.create(
                    export=self,
                    case=case,
                )

    @property
    def all_cases(self) -> list[Case]:
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
    base_case = models.ForeignKey(
        BaseCase,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.UNREADY)

    class Meta:
        ordering: list[str] = ["id"]

    def __str__(self) -> str:
        return f"{self.export}: {self.case}"
