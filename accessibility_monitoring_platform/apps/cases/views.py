"""
Views for cases app
"""

from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..common.utils import (
    check_dict_for_truthy_values,
    get_dict_without_page_items,
    get_url_parameters_for_pagination,
    replace_search_key_with_case_search,
)
from ..common.views import HideCaseNavigationMixin
from .forms import (
    CaseFileDeleteForm,
    CaseFileUpdateForm,
    CaseSearchForm,
    FileUploadForm,
)
from .models import BaseCase, CaseFile
from .record_event import record_create_event
from .utils import S3ReadWriteFile, filter_cases

AUDITOR_SEARCH_FIELDS: list[str] = [
    "auditor",
    "reviewer",
]
DATE_SEARCH_FIELDS: list[str] = [
    "date_start_0",
    "date_start_1",
    "date_start_2",
    "date_end_0",
    "date_end_1",
    "date_end_2",
]
METADATA_SEARCH_FIELDS: list[str] = [
    "status",
    "case_number",
    "recommendation_for_enforcement",
    "sector",
    "is_complaint",
    "enforcement_body",
    "subcategory",
]
TRUTHY_SEARCH_FIELDS: list[str] = (
    [
        "sort_by",
        "test_type",
    ]
    + AUDITOR_SEARCH_FIELDS
    + DATE_SEARCH_FIELDS
    + METADATA_SEARCH_FIELDS
)


class CaseFileUploadMixin:
    def case_file_upload(
        self,
        uploaded_file: InMemoryUploadedFile,
        user: User,
        base_case: BaseCase,
        file_type: CaseFile.Type = CaseFile.Type.STATEMENT,
    ) -> None:
        """Save uploaded file to S3"""
        case_file: CaseFile = CaseFile.objects.create(
            name=uploaded_file.name,
            type=file_type,
            uploaded_by=user,
            base_case=base_case,
        )
        s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
        s3_read_write.write_case_file_to_s3(
            case_file=case_file,
            file_content=uploaded_file,
        )
        record_create_event(
            user=user,
            model_object=case_file,
            base_case=case_file.base_case,
        )


class CaseListView(ListView):
    """
    View of list of cases
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "base_cases"
    paginate_by: int = 20
    template_name: str = "cases/basecase_list.html"

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.form: CaseSearchForm = CaseSearchForm(
                replace_search_key_with_case_search(self.request.GET)
            )
            self.form.is_valid()
        else:
            self.form = CaseSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[BaseCase]:
        """Add filters to queryset"""
        if self.form.errors:
            return BaseCase.objects.none()

        return filter_cases(self.form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)

        filter_fields: dict[str, str] = get_dict_without_page_items(
            self.request.GET.items()
        )
        context["auditor_search_open"] = check_dict_for_truthy_values(
            dictionary=filter_fields,
            keys_to_check=AUDITOR_SEARCH_FIELDS,
        )
        context["date_search_open"] = check_dict_for_truthy_values(
            dictionary=filter_fields,
            keys_to_check=DATE_SEARCH_FIELDS,
        )
        context["metadata_search_open"] = check_dict_for_truthy_values(
            dictionary=filter_fields,
            keys_to_check=METADATA_SEARCH_FIELDS,
        )
        context["advanced_search_open"] = check_dict_for_truthy_values(
            dictionary=filter_fields,
            keys_to_check=TRUTHY_SEARCH_FIELDS,
        )
        context["form"] = self.form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context


class CaseFileListView(HideCaseNavigationMixin, DetailView):
    """
    View of Documents for a case
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "case"
    template_name: str = "cases/case_file_list.html"


class CaseFileUploadView(HideCaseNavigationMixin, CaseFileUploadMixin, FormView):
    """View to upload a case file"""

    form_class: type[FileUploadForm] = FileUploadForm
    template_name: str = "cases/forms/case_file_create.html"

    def form_valid(self, form: forms.ModelForm) -> HttpResponseRedirect:
        """Process contents of file upload"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        uploaded_file: InMemoryUploadedFile | None = form.cleaned_data["file_to_upload"]
        if uploaded_file is not None:
            self.case_file_upload(
                uploaded_file=uploaded_file,
                user=self.request.user,
                base_case=base_case,
                file_type=form.cleaned_data["type"],
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to document list page on exit"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        case_pk: dict[str, int] = {"pk": base_case.id}
        return reverse("cases:case-file-list", kwargs=case_pk)


class CaseFileUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to update a case file"""

    model: type[CaseFile] = CaseFile
    context_object_name: str = "case_file"
    template_name: str = "cases/forms/case_file_update.html"
    form_class: type[CaseFileUpdateForm] = CaseFileUpdateForm

    def get_success_url(self) -> str:
        """Return to document list page on exit"""
        case_file: CaseFile = self.object
        case_pk: dict[str, int] = {"pk": case_file.base_case.id}
        return reverse("cases:case-file-list", kwargs=case_pk)


class CaseFileDeleteView(CaseFileUpdateView):
    """View to delete a case file"""

    template_name: str = "cases/forms/case_file_delete.html"
    form_class: type[CaseFileDeleteForm] = CaseFileDeleteForm


def case_file_download(request: HttpRequest, pk: int) -> FileResponse | HttpResponse:
    """Download case file from S3"""
    case_file: CaseFile = get_object_or_404(CaseFile, id=pk)
    s3_read_write: S3ReadWriteFile = S3ReadWriteFile()
    file_to_download: bytes | str = s3_read_write.read_case_file_from_s3(
        case_file=case_file
    )
    if isinstance(file_to_download, str):
        return HttpResponse(file_to_download)
    return FileResponse(ContentFile(file_to_download, case_file.name))
