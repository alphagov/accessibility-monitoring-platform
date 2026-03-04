"""
Views for cases app
"""

from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
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
from .forms import CaseSearchForm, DocumentUploadForm, DocumentUpdateForm
from .models import BaseCase, Document
from .record_event import record_create_event, record_update_event
from .utils import (
    filter_cases,
    S3ReadWriteDocument,
)

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


class DocumentListView(HideCaseNavigationMixin, DetailView):
    """
    View of Documents for a case
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "case"
    template_name: str = "cases/document_list.html"


class DocumentCreateView(HideCaseNavigationMixin, FormView):
    """View to upload a Document"""

    form_class: type[DocumentUploadForm] = DocumentUploadForm
    template_name: str = "cases/forms/document_create.html"

    def form_valid(self, form: forms.ModelForm) -> HttpResponseRedirect:
        """Process contents of file upload"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        uploaded_file: InMemoryUploadedFile = form.cleaned_data["file_to_upload"]
        document: Document | None = base_case.documents.filter(
            name=uploaded_file.name
        ).first()
        if document is None:
            document: Document = Document.objects.create(
                name=uploaded_file.name,
                type=form.cleaned_data["type"],
                uploaded_by=self.request.user,
                base_case=base_case,
            )
        s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
        if s3_read_write.check_document_on_s3(document=document) is True:
            document.version += 1
            document.save()
        s3_read_write.put_document_to_s3(
            document=document,
            file_content=uploaded_file,
        )
        user: User = self.request.user
        record_create_event(
            user=user,
            model_object=document,
            base_case=document.base_case,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to document list page on exit"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("pk"))
        case_pk: dict[str, int] = {"pk": base_case.id}
        return reverse("cases:document-list", kwargs=case_pk)


class DocumentUpdateView(HideCaseNavigationMixin, FormView):

    form_class: type[DocumentUpdateForm] = DocumentUpdateForm
    template_name: str = "cases/forms/document_update.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["document"] = get_object_or_404(Document, id=self.kwargs.get("pk"))
        return context

    def form_valid(self, form: forms.ModelForm) -> HttpResponseRedirect:
        """Add update event"""
        if form.changed_data:
            document: Document = get_object_or_404(Document, id=self.kwargs.get("pk"))
            user: User = self.request.user
            document.uploaded_by = user
            document.type = form.cleaned_data["type"]
            if "file_to_upload" in form.cleaned_data:
                uploaded_file = form.cleaned_data["file_to_upload"]
                document.name = uploaded_file.name
                s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
                if s3_read_write.check_document_on_s3(document=document) is True:
                    document.version += 1
                s3_read_write.put_document_to_s3(
                    document=document,
                    file_content=uploaded_file,
                )
            record_update_event(
                user=user,
                model_object=document,
                base_case=document.base_case,
            )
            document.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to document list page on save"""
        document: Document = get_object_or_404(Document, id=self.kwargs.get("pk"))
        case_pk: dict[str, int] = {"pk": document.base_case.id}
        return reverse("cases:document-list", kwargs=case_pk)


def document_download(request: HttpRequest, pk: int) -> HttpResponse:
    """Download document from S3"""
    document: Document = get_object_or_404(Document, id=pk)
    s3_read_write: S3ReadWriteDocument = S3ReadWriteDocument()
    file_to_download = s3_read_write.get_document_from_s3(document=document)
    return HttpResponse(
        file_to_download,
        content_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={document.name}",
            "Cache-Control": "no-cache",
        },
    )
