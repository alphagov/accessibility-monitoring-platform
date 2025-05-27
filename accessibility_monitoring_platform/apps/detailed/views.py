"""
Views for cases app
"""

from typing import Any

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from ..common.utils import extract_domain_from_url, get_url_parameters_for_pagination
from ..common.views import HideCaseNavigationMixin, ShowGoBackJSWidgetMixin
from .forms import (
    DetailedCaseCreateForm,
    DetailedCaseHistoryCreateForm,
    DetailedCaseMetadataUpdateForm,
    DetailedCaseSearchForm,
    DetailedCaseStatusUpdateForm,
)
from .models import DetailedCase, DetailedCaseHistory
from .utils import (
    add_to_detailed_case_status_history,
    record_model_create_event,
    record_model_update_event,
)


def find_duplicate_cases(
    url: str, organisation_name: str = ""
) -> QuerySet[DetailedCase]:
    """Look for cases with matching domain or organisation name"""
    domain: str = extract_domain_from_url(url)
    return DetailedCase.objects.filter(
        Q(organisation_name__icontains=organisation_name) | Q(domain=domain)
    )


class DetailedCaseCreateView(ShowGoBackJSWidgetMixin, CreateView):
    """
    View to create a case
    """

    model: type[DetailedCase] = DetailedCase
    form_class: type[DetailedCaseCreateForm] = DetailedCaseCreateForm
    context_object_name: str = "detailed_case"
    template_name: str = "detailed/forms/create.html"

    def form_valid(self, form: DetailedCaseCreateForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            detailed_case: DetailedCase = form.save(commit=False)
            detailed_case.created_by = self.request.user
            return super().form_valid(form)

        context: dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[DetailedCase] = find_duplicate_cases(
            url=form.cleaned_data.get("home_page_url", ""),
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)

        detailed_case: DetailedCase = form.save(commit=False)
        detailed_case.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        detailed_case: DetailedCase = self.object
        user: User = self.request.user
        record_model_create_event(
            user=user, model_object=detailed_case, detailed_case=detailed_case
        )
        case_pk: dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("detailed:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("detailed:case-create")
        else:
            url: str = reverse("detailed:case-list")
        return url


class DetailedCaseDetailView(DetailView):
    """View of details of a single detailed Case"""

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "detailed_case"


class DetailedCaseListView(ListView):
    """
    View of list of cases
    """

    model: type[DetailedCase] = DetailedCase
    context_object_name: str = "detailed_cases"
    paginate_by: int = 10

    def get(self, request, *args, **kwargs):
        """Populate filter form"""
        if self.request.GET:
            self.form: DetailedCaseSearchForm = DetailedCaseSearchForm(self.request.GET)
            self.form.is_valid()
        else:
            self.form = DetailedCaseSearchForm()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[DetailedCase]:
        """Add filters to queryset"""
        if self.form.errors:
            return DetailedCase.objects.none()
        if hasattr(self.form, "cleaned_data"):
            search: str = self.form.cleaned_data.get("case_search", "")
            case_number: int = int(search) if search.isnumeric() else 0
            if search:
                return DetailedCase.objects.filter(
                    Q(organisation_name__icontains=search)
                    | Q(domain__icontains=search)
                    | Q(case_number=case_number)
                )
        return DetailedCase.objects.all()

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["url_parameters"] = get_url_parameters_for_pagination(
            request=self.request
        )
        return context


class DetailedCaseMetadataUpdateView(UpdateView):
    """View to update detailed case metadata"""

    model: type[DetailedCase] = DetailedCase
    form_class: type[DetailedCaseMetadataUpdateForm] = DetailedCaseMetadataUpdateForm
    context_object_name: str = "detailed_case"
    template_name: str = "detailed/forms/case_form.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: DetailedCase = form.save(commit=False)
            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)

            user: User = self.request.user
            record_model_update_event(
                user=user, model_object=self.object, detailed_case=self.object
            )

            self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return self.object.get_absolute_url()
        return self.request.path


class DetailedCaseStatusUpdateView(HideCaseNavigationMixin, UpdateView):
    """View to update detailed case status"""

    model: type[DetailedCase] = DetailedCase
    form_class: type[DetailedCaseStatusUpdateForm] = DetailedCaseStatusUpdateForm
    context_object_name: str = "detailed_case"
    template_name: str = "detailed/forms/case_status.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: DetailedCase = form.save(commit=False)
            user: User = self.request.user
            record_model_update_event(
                user=user, model_object=self.object, detailed_case=self.object
            )
            self.object.save()
            add_to_detailed_case_status_history(detailed_case=self.object, user=user)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Stay on page"""
        return self.request.path


class DetailedCaseNoteCreateView(HideCaseNavigationMixin, CreateView):
    """View to add a note to the DetailedCaseHistory"""

    model: type[DetailedCaseHistory] = DetailedCaseHistory
    form_class: type[DetailedCaseHistoryCreateForm] = DetailedCaseHistoryCreateForm
    context_object_name: str = "detailed_case_history"
    template_name: str = "detailed/forms/note_create.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["detailed_case"] = detailed_case
        context["detailed_case_history"] = detailed_case.detailedcasehistory_set.all()
        return context

    def form_valid(self, form: DetailedCaseCreateForm):
        """Process contents of valid form"""
        detailed_case: DetailedCase = get_object_or_404(
            DetailedCase, id=self.kwargs.get("case_id")
        )
        detailed_case_history: DetailedCaseHistory = form.save(commit=False)
        detailed_case_history.detailed_case = detailed_case
        detailed_case_history.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        detailed_case_history: DetailedCaseHistory = self.object
        detailed_case: DetailedCase = detailed_case_history.detailed_case
        user: User = self.request.user
        record_model_create_event(
            user=user,
            model_object=detailed_case_history,
            detailed_case=detailed_case,
        )
        return reverse(
            "detailed:create-case-note", kwargs={"case_id": detailed_case.id}
        )
