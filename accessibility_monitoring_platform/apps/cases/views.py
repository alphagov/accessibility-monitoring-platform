"""
Views for cases app
"""

from typing import Any

from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..common.utils import (
    check_dict_for_truthy_values,
    get_dict_without_page_items,
    get_url_parameters_for_pagination,
    replace_search_key_with_case_search,
)
from .forms import CaseSearchForm, BaseCaseDocumentCreateUpdateForm
from .models import BaseCase, Document
from .utils import filter_cases

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


class DocumentListView(DetailView):
    """
    View of Documents for a case
    """

    model: type[BaseCase] = BaseCase
    context_object_name: str = "case"
    template_name: str = "cases/document_list.html"


class DocumentCreateView(CreateView):
    """
    View to create a Document ticket
    """

    model: type[Document] = Document
    form_class: type[BaseCaseDocumentCreateUpdateForm] = (
        BaseCaseDocumentCreateUpdateForm
    )
    template_name: str = "cases/forms/document_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case to context as object"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("case_id"))
        context["case"] = base_case
        context["object"] = base_case
        return context

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Process contents of file upload"""
        base_case: BaseCase = get_object_or_404(BaseCase, id=self.kwargs.get("case_id"))
        form: forms.Form = self.form_class(request.POST, request.FILES)
        breakpoint()
        if form.is_valid():
            uploaded_file: InMemoryUploadedFile = request.FILES["document_to_upload"]
            file_name: str = uploaded_file.name
            document: Document = Document(
                name=file_name,
                document_type=form.cleaned_data["document_type"],
                uploaded_by=request.user,
                base_case=base_case,
            )
            # check s3 for matching document
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        document: Document = self.object
        # user: User = self.request.user
        # record_base_case_model_create_event(
        #     user=user,
        #     model_object=document,
        #     base_case=document.base_case,
        # )
        case_pk: dict[str, int] = {"pk": document.base_case.id}
        return reverse("case:document-list", kwargs=case_pk)


class DocumentUpdateView(UpdateView):

    model: type[Document] = Document
    form_class: type[BaseCaseDocumentCreateUpdateForm] = (
        BaseCaseDocumentCreateUpdateForm
    )
    context_object_name: str = "document"
    template_name: str = "cases/forms/document_update.html"

    def form_valid(self, form: forms.ModelForm) -> HttpResponseRedirect:
        """Add update event"""
        if form.changed_data:
            # document: Document = form.save(commit=False)
            # user: User = self.request.user
            # record_base_case_model_update_event(
            #     user=user,
            #     model_object=document,
            #     simplified_case=document.simplified_case,
            # )
            self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Return to zendesk tickets page on save"""
        document: Document = self.object
        case_pk: dict[str, int] = {"case_id": document.simplified_case.id}
        return reverse("cases:document-list", kwargs=case_pk)


# class DocumentConfirmDeleteUpdateView(DocumentUpdateView):
#     """
#     View to confirm delete of Zendesk ticket
#     """

#     form_class: type[DocumentConfirmDeleteUpdateForm] = (
#         DocumentConfirmDeleteUpdateForm
#     )
#     template_name: str = "simplified/forms/zendesk_ticket_confirm_delete.html"
