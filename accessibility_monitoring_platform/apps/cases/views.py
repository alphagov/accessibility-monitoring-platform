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
    CaseSearchForm,
    DocumentUploadDeleteForm,
    DocumentUploadForm,
    DocumentUploadUpdateForm,
)
from .models import BaseCase, DocumentUpload
from .record_event import record_create_event
from .utils import S3ReadWriteDocument, filter_cases

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


class DocumentUploadMixin:
    def document_upload(
        self,
        uploaded_file: InMemoryUploadedFile,
        user: User,
        base_case: BaseCase,
        document_type: DocumentUpload.Type = DocumentUpload.Type.STATEMENT,
    ) -> None:
        """Save uploaded file to S3"""
        document_upload: DocumentUpload = DocumentUpload.objects.create(
            name=uploaded_file.name,
            type=document_type,
            uploaded_by=user,
            base_case=base_case,
        )
        s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
        s3_read_write.put_document_to_s3(
            document_upload=document_upload,
            file_content=uploaded_file,
        )
        record_create_event(
            user=user,
            model_object=document_upload,
            base_case=document_upload.base_case,
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


class DocumentUploadListView(HideCaseNavigationMixin, DetailView):
    """
    View of Documents for a case
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "case"
    template_name: str = "cases/document_upload_list.html"


class DocumentUploadView(HideCaseNavigationMixin, DocumentUploadMixin, FormView):
    """View to upload a Document upload"""

    form_class: type[DocumentUploadForm] = DocumentUploadForm
    template_name: str = "cases/forms/document_upload_create.html"

    def form_valid(self, form: forms.ModelForm) -> HttpResponseRedirect:
        """Process contents of file upload"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        uploaded_file: InMemoryUploadedFile | None = form.cleaned_data["file_to_upload"]
        if uploaded_file is not None:
            self.document_upload(
                uploaded_file=uploaded_file,
                user=self.request.user,
                base_case=base_case,
                document_type=form.cleaned_data["type"],
            )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to document list page on exit"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        case_pk: dict[str, int] = {"pk": base_case.id}
        return reverse("cases:document-upload-list", kwargs=case_pk)


class DocumentUploadUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to update a Document upload"""

    model: type[DocumentUpload] = DocumentUpload
    context_object_name: str = "document_upload"
    template_name: str = "cases/forms/document_upload_update.html"
    form_class: type[DocumentUploadUpdateForm] = DocumentUploadUpdateForm

    def get_success_url(self) -> str:
        """Return to document list page on exit"""
        document_upload: DocumentUpload = self.object
        case_pk: dict[str, int] = {"pk": document_upload.base_case.id}
        return reverse("cases:document-upload-list", kwargs=case_pk)


class DocumentUploadDeleteView(DocumentUploadUpdateView):
    """View to delete a Document upload"""

    template_name: str = "cases/forms/document_upload_delete.html"
    form_class: type[DocumentUploadDeleteForm] = DocumentUploadDeleteForm


def document_download(request: HttpRequest, pk: int) -> FileResponse | HttpResponse:
    """Download document upload from S3"""
    document_upload: DocumentUpload = get_object_or_404(DocumentUpload, id=pk)
    s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
    file_to_download: bytes | str = s3_read_write.get_document_from_s3(
        document_upload=document_upload
    )
    if isinstance(file_to_download, str):
        return HttpResponse(file_to_download)
    return FileResponse(ContentFile(file_to_download, document_upload.name))
