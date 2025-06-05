"""
Views for cases app
"""

from typing import Any

from django.contrib.auth.models import User
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from ..common.utils import extract_domain_from_url
from ..common.views import ShowGoBackJSWidgetMixin
from .forms import MobileCaseCreateForm, MobileCaseMetadataUpdateForm
from .models import MobileCase
from .utils import record_model_create_event, record_model_update_event


def find_duplicate_cases(organisation_name: str = "") -> QuerySet[MobileCase]:
    """Look for cases with matching domain or organisation name"""
    return MobileCase.objects.filter(organisation_name__icontains=organisation_name)


class MobileCaseCreateView(ShowGoBackJSWidgetMixin, CreateView):
    """
    View to create a case
    """

    model: type[MobileCase] = MobileCase
    form_class: type[MobileCaseCreateForm] = MobileCaseCreateForm
    context_object_name: str = "mobile_case"
    template_name: str = "mobile/forms/create.html"

    def form_valid(self, form: MobileCaseCreateForm):
        """Process contents of valid form"""
        if "allow_duplicate_cases" in self.request.GET:
            mobile_case: MobileCase = form.save(commit=False)
            mobile_case.created_by = self.request.user
            mobile_case.test_type = MobileCase.TestType.MOBILE
            return super().form_valid(form)

        context: dict[str, Any] = self.get_context_data()
        duplicate_cases: QuerySet[MobileCase] = find_duplicate_cases(
            organisation_name=form.cleaned_data.get("organisation_name", ""),
        ).order_by("created")

        if duplicate_cases:
            context["duplicate_cases"] = duplicate_cases
            context["new_case"] = form.save(commit=False)
            return self.render_to_response(context)

        mobile_case: MobileCase = form.save(commit=False)
        mobile_case.created_by = self.request.user
        mobile_case.test_type = MobileCase.TestType.MOBILE
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        mobile_case: MobileCase = self.object
        user: User = self.request.user
        record_model_create_event(
            user=user, model_object=mobile_case, mobile_case=mobile_case
        )
        case_pk: dict[str, int] = {"pk": self.object.id}
        if "save_continue_case" in self.request.POST:
            url: str = reverse("mobile:edit-case-metadata", kwargs=case_pk)
        elif "save_new_case" in self.request.POST:
            url: str = reverse("mobile:case-create")
        else:
            url: str = reverse("cases:case-list")
        return url


class MobileCaseDetailView(DetailView):
    """View of details of a single mobile Case"""

    model: type[MobileCase] = MobileCase
    context_object_name: str = "mobile_case"


class MobileCaseMetadataUpdateView(UpdateView):
    """View to update mobile case metadata"""

    model: type[MobileCase] = MobileCase
    form_class: type[MobileCaseMetadataUpdateForm] = MobileCaseMetadataUpdateForm
    context_object_name: str = "mobile_case"
    template_name: str = "mobile/forms/mobilecase_form.html"

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        """Add message on change of case"""
        if form.changed_data:
            self.object: MobileCase = form.save(commit=False)
            if "home_page_url" in form.changed_data:
                self.object.domain = extract_domain_from_url(self.object.home_page_url)

            user: User = self.request.user
            record_model_update_event(
                user=user, model_object=self.object, mobile_case=self.object
            )

            self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return self.object.get_absolute_url()
        return self.request.path
