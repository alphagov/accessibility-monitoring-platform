"""
Views for cases
"""
import re
import urllib

from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Case, Contact
from .forms import CaseWebsiteDetailUpdateForm, ContactFormset, ContactFormsetOneExtra, SearchForm, TestResultsUpdateForm

DEFAULT_SORT = "-id"


def get_id_from_button_name(button_name_prefix, post):
    encoded_url = urllib.parse.urlencode(post)
    match_obj = re.search(r"" + button_name_prefix + "\d+", encoded_url)
    id = None
    if match_obj is not None:
        button_name = match_obj.group()
        id = int(button_name.replace(button_name_prefix, ""))
    return id


class CaseDetailView(DetailView):
    model = Case
    context_object_name = "case"

    def get_context_data(self, **kwargs):
        """ Add unarchived contacts context """
        context = super().get_context_data(**kwargs)
        context["contacts"] = self.object.contact_set.filter(archived=False)
        return context


class CaseListView(ListView):
    model = Case
    context_object_name = "cases"
    paginate_by = 10

    def get_queryset(self):
        """ Add filters to queryset """
        filters = {}
        form = SearchForm(self.request.GET)
        form.is_valid()
        case_number = form.cleaned_data.get("case_number")
        if case_number:
            filters["id"] = case_number
        domain = form.cleaned_data.get("domain")
        if domain:
            filters["domain__icontains"] = domain
        organisation = form.cleaned_data.get("organisation")
        if organisation:
            filters["organisation_name__icontains"] = organisation
        auditor = form.cleaned_data.get("auditor")
        if auditor:
            filters["auditor"] = auditor
        status = form.cleaned_data.get("status")
        if status:
            filters["status"] = status
        filters["created__gte"] = form.start_date
        filters["created__lte"] = form.end_date
        sort_by = form.cleaned_data.get("sort_by", DEFAULT_SORT)
        if not sort_by:
            sort_by = DEFAULT_SORT
        return Case.objects.filter(**filters).order_by(sort_by)

    def get_context_data(self, **kwargs):
        """ Add field values into context """
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        get_without_page: dict = {
            key: value for (key, value) in self.request.GET.items() if key != "page"
        }
        context["parameters"] = urllib.parse.urlencode(get_without_page)
        context["case_number"] = self.request.GET.get("case-number", "")
        context["auditor"] = self.request.GET.get("auditor", "")
        return context


class CaseWebsiteDetailUpdateView(UpdateView):
    model = Case
    form_class = CaseWebsiteDetailUpdateForm
    context_object_name = "case"
    template_name_suffix = "_website_details_update_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-contact-details", kwargs={"pk": self.object.id}
            )
        return url


class CaseContactFormsetUpdateView(UpdateView):
    model = Case
    fields = []
    context_object_name = "case"
    template_name = "cases/case_contact_formset.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            contacts_formset = ContactFormset(self.request.POST)
        else:
            contacts = self.object.contact_set.filter(archived=False)
            if "add_extra" in self.request.GET:
                contacts_formset = ContactFormsetOneExtra(queryset=contacts)
            else:
                contacts_formset = ContactFormset(queryset=contacts)
        context["contacts_formset"] = contacts_formset
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context["contacts_formset"]
        case = form.save()
        if contact_formset.is_valid():
            contacts = contact_formset.save(commit=False)
            for contact in contacts:
                if not contact.case_id:
                    contact.case_id = case.id
                contact.save()
        contact_id_to_archive = get_id_from_button_name(
            "remove_contact_", self.request.POST
        )
        if contact_id_to_archive is not None:
            contact_to_archive = Contact.objects.get(id=contact_id_to_archive)
            contact_to_archive.archived = True
            contact_to_archive.save()
        return super().form_valid(form)

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy(
                "cases:case-detail", kwargs={"pk": self.object.id}
            )
        elif "save_continue" in self.request.POST:
            url = reverse_lazy(
                "cases:edit-test-results", kwargs={"pk": self.object.id}
            )
        else:
            url = reverse_lazy("cases:case-list")
        return url


class CaseTestResultsUpdateView(UpdateView):
    model = Case
    form_class = TestResultsUpdateForm
    context_object_name = "case"
    template_name_suffix = "_test_results_update_form"

    def get_success_url(self):
        """ Detect the submit button used and act accordingly """
        if "save_exit" in self.request.POST:
            url = reverse_lazy("cases:case-detail", kwargs={"pk": self.object.id})
        else:
            url = reverse_lazy(
                "cases:edit-test-results", kwargs={"pk": self.object.id}
            )
        return url