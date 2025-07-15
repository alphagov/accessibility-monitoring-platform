"""
Common views
"""

import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.mail import EmailMessage
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import BaseCase
from ..common.sitemap import PlatformPage, Sitemap
from ..detailed.models import DetailedCase
from ..detailed.utils import import_detailed_cases_csv
from ..mobile.utils import import_mobile_cases_csv
from ..reports.models import Report
from ..simplified.models import SimplifiedCase
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from .forms import (
    ActiveQAAuditorUpdateForm,
    AMPContactAdminForm,
    AMPIssueReportForm,
    BulkURLSearchForm,
    FooterLinkFormset,
    FooterLinkOneExtraFormset,
    FrequentlyUsedLinkFormset,
    FrequentlyUsedLinkOneExtraFormset,
    ImportCSVForm,
    PlatformCheckingForm,
)
from .mark_deleted_util import mark_object_as_deleted
from .metrics import (
    get_case_progress_metrics,
    get_case_yearly_metrics,
    get_equality_body_cases_metric,
    get_policy_progress_metrics,
    get_policy_total_metrics,
    get_policy_yearly_metrics,
    get_report_progress_metrics,
    get_report_yearly_metrics,
)
from .models import (
    ChangeToPlatform,
    FooterLink,
    FrequentlyUsedLink,
    IssueReport,
    Platform,
)
from .platform_template_view import PlatformTemplateView
from .utils import extract_domain_from_url, get_platform_settings, sanitise_domain

logger = logging.getLogger(__name__)


class HideCaseNavigationMixin:
    """
    Mixin for Case pages which hides the Case navigation and makes page contents full
    width.
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["amp_hide_case_nav"] = True
        return context


class ShowGoBackJSWidgetMixin:
    """
    Mixin for Case pages which enables the JS widget to go back to previous page in
    browser history.
    """

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["amp_show_go_back"] = True
        return context


class NextPlatformPageMixin:
    """
    Mixin for UpdateViews with Save and continue buttons which returns next platform
    page, adds it to context and returns its URL on success.
    """

    def get_next_platform_page(self) -> PlatformPage:
        sitemap: Sitemap = Sitemap(request=self.request)
        next_platform_page: PlatformPage = sitemap.current_platform_page.next_page
        if next_platform_page is not None:
            next_platform_page.set_instance(instance=self.object)
        return next_platform_page

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["next_platform_pages"] = [self.get_next_platform_page()]
        return context

    def get_success_url(self) -> str:
        """Detect the submit button used and act accordingly"""
        if "save_continue" in self.request.POST:
            return self.get_next_platform_page().url
        return self.request.path


class ContactAdminView(FormView):
    """
    Send email to platform admin
    """

    form_class = AMPContactAdminForm
    template_name: str = "common/contact_admin.html"
    success_url: str = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        self.send_mail(form.cleaned_data)
        return super().form_valid(form)

    def send_mail(self, cleaned_data: dict[str, str]) -> None:
        subject: str = cleaned_data.get("subject", "")
        message: str = cleaned_data.get("message", "")
        if subject or message:
            email: EmailMessage = EmailMessage(
                subject=subject,
                body=message,
                from_email=self.request.user.email,
                to=[settings.CONTACT_ADMIN_EMAIL],
            )
            email.send()


class IssueReportView(FormView):
    """
    Save user feedback
    """

    form_class: type[AMPIssueReportForm] = AMPIssueReportForm
    template_name: str = "common/issue_report.html"
    success_url: str = reverse_lazy("dashboard:home")

    def get(self, request, *args, **kwargs):
        """Populate form"""
        target_page_url: str = self.request.GET.get("page_url", "")
        target_page_title: str = self.request.GET.get("page_title", "Unknown page")

        goal_description: str = self.request.GET.get("goal_description", "")
        issue_description: str = self.request.GET.get("issue_description", "")
        self.form: AMPIssueReportForm = self.form_class(
            {
                "page_url": target_page_url,
                "page_title": target_page_title,
                "goal_description": goal_description,
                "issue_description": issue_description,
            }
        )
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add field values into context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["form"] = self.form
        return context

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        issue_report: IssueReport = form.save(commit=False)
        issue_report.created_by = self.request.user
        issue_report.save()
        self.send_mail(issue_report)
        return redirect(issue_report.page_url)

    def send_mail(self, issue_report: IssueReport) -> None:
        email: EmailMessage = EmailMessage(
            subject=f"Platform issue on {issue_report.page_title}",
            body=f"""Reported by: {issue_report.created_by}

URL: https://{self.request.get_host()}{issue_report.page_url}

Goal: {issue_report.goal_description}

Issue: {issue_report.issue_description}""",
            from_email=self.request.user.email,
            to=[settings.CONTACT_ADMIN_EMAIL],
        )
        email.send()


class ActiveQAAuditorUpdateView(UpdateView):
    """
    Update active QA auditor
    """

    model: type[Platform] = Platform
    context_object_name: str = "platform"
    form_class: type[ActiveQAAuditorUpdateForm] = ActiveQAAuditorUpdateForm
    template_name: str = "common/settings/active_qa_auditor.html"

    def get_object(self) -> Platform:
        """Return the platform-wide settings"""
        return get_platform_settings()

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        messages.success(self.request, "Active QA auditor has been updated")
        return self.request.path


class ChangeToPlatformListView(ListView):
    """
    View of list of platform changes
    """

    model: type[ChangeToPlatform] = ChangeToPlatform
    template_name: str = "common/settings/platform_history.html"
    context_object_name: str = "changes_to_platform"
    paginate_by: int = 10


class AccessibilityStatementTemplateView(PlatformTemplateView):
    template_name: str = "common/accessibility_statement.html"


class PrivacyNoticeTemplateView(PlatformTemplateView):
    template_name: str = "common/privacy_notice.html"


class MarkdownCheatsheetTemplateView(PlatformTemplateView):
    template_name: str = "common/settings/markdown_cheatsheet.html"


class MoreInformationTemplateView(PlatformTemplateView):
    template_name: str = "common/settings/more_information.html"


class MetricsCaseTemplateView(TemplateView):
    """
    View of case metrics
    """

    template_name: str = "common/metrics/case.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add number of cases to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        extra_context: dict[str, Any] = {
            "progress_metrics": get_case_progress_metrics(),
            "yearly_metrics": get_case_yearly_metrics(),
        }
        return {**extra_context, **context}


class MetricsPolicyTemplateView(TemplateView):
    """
    View of policy metrics
    """

    template_name: str = "common/metrics/policy.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add number of cases to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        extra_context: dict[str, Any] = {
            "total_metrics": get_policy_total_metrics(),
            "progress_metrics": get_policy_progress_metrics(),
            "equality_body_cases_metric": get_equality_body_cases_metric(),
            "yearly_metrics": get_policy_yearly_metrics(),
        }
        return {**extra_context, **context}


class MetricsReportTemplateView(TemplateView):
    """
    View of report metrics
    """

    template_name: str = "common/metrics/report.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add number of cases to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        extra_context: dict[str, Any] = {
            "progress_metrics": get_report_progress_metrics(),
            "yearly_metrics": get_report_yearly_metrics(),
        }
        return {**extra_context, **context}


class FrequentlyUsedLinkFormsetTemplateView(TemplateView):
    """
    Update list of frequently used links
    """

    template_name: str = "common/settings/edit_frequently_used_links.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            links_formset = FrequentlyUsedLinkFormset(self.request.POST)
        else:
            links: QuerySet[FrequentlyUsedLink] = FrequentlyUsedLink.objects.filter(
                is_deleted=False
            )
            if "add_link" in self.request.GET:
                links_formset = FrequentlyUsedLinkOneExtraFormset(queryset=links)
            else:
                links_formset = FrequentlyUsedLinkFormset(queryset=links)
        context["links_formset"] = links_formset
        return context

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        links_formset = context["links_formset"]
        if links_formset.is_valid():
            links: list[FrequentlyUsedLink] = links_formset.save(commit=False)
            for link in links:
                if not link.id:
                    link.save()
                    record_simplified_model_create_event(
                        user=self.request.user, model_object=link
                    )
                else:
                    record_simplified_model_update_event(
                        user=self.request.user, model_object=link
                    )
                    link.save()
        else:
            return self.render_to_response(
                self.get_context_data(links_formset=links_formset)
            )
        mark_object_as_deleted(
            request=request,
            delete_button_prefix="remove_link_",
            object_to_delete_model=FrequentlyUsedLink,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        url: str = reverse_lazy("common:edit-frequently-used-links")
        if "add_link" in self.request.POST:
            return f"{url}?add_link=true#link-None"
        return url


class FooterLinkFormsetTemplateView(TemplateView):
    """
    Update list of footer links
    """

    template_name: str = "common/settings/edit_footer_links.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        if self.request.POST:
            links_formset = FooterLinkFormset(self.request.POST)
        else:
            links: QuerySet[FooterLink] = FooterLink.objects.filter(is_deleted=False)
            if "add_link" in self.request.GET:
                links_formset = FooterLinkOneExtraFormset(queryset=links)
            else:
                links_formset = FooterLinkFormset(queryset=links)
        context["links_formset"] = links_formset
        return context

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect | HttpResponse:
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        links_formset = context["links_formset"]
        if links_formset.is_valid():
            links: list[FooterLink] = links_formset.save(commit=False)
            for link in links:
                if not link.id:
                    link.save()
                    record_simplified_model_create_event(
                        user=self.request.user, model_object=link
                    )
                else:
                    record_simplified_model_update_event(
                        user=self.request.user, model_object=link
                    )
                    link.save()
        else:
            return self.render_to_response(
                self.get_context_data(links_formset=links_formset)
            )

        mark_object_as_deleted(
            request=request,
            delete_button_prefix="remove_link_",
            object_to_delete_model=FooterLink,
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        url: str = reverse_lazy("common:edit-footer-links")
        if "add_link" in self.request.POST:
            return f"{url}?add_link=true#link-None"
        return url


class PlatformCheckingView(UserPassesTestMixin, FormView):
    """
    Write log message
    """

    form_class = PlatformCheckingForm
    template_name: str = "common/tech_team/platform_checking.html"
    success_url: str = reverse_lazy("common:platform-checking")

    def test_func(self):
        """Only staff users have access to this view"""
        return self.request.user.is_staff

    def form_valid(self, form):
        if "trigger_400" in self.request.POST:
            raise BadRequest
        if "trigger_403" in self.request.POST:
            raise PermissionDenied
        if "trigger_500" in self.request.POST:
            1 / 0
        logger.log(
            level=int(form.cleaned_data["level"]), msg=form.cleaned_data["message"]
        )
        return super().form_valid(form)


class ReferenceImplementaionView(TemplateView):
    """Reference implementations of reusable components"""

    template_name: str = "common/tech_team/reference_implementation.html"

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        report: Report | None = Report.objects.all().first()
        if report is None or not hasattr(
            report.base_case, "simplifiedcase"
        ):  # In test environment
            simplified_case: SimplifiedCase | None = (
                SimplifiedCase.objects.all().first()
            )
        else:
            simplified_case: SimplifiedCase = report.base_case.simplifiedcase
        context["case"] = simplified_case
        context["detailed_case"] = DetailedCase.objects.last()
        return context


class IssueReportListView(ListView):
    """
    View of list of issue reports.
    """

    model: type[IssueReport] = IssueReport
    template_name: str = "common/issue_report_list.html"
    context_object_name: str = "issue_reports"
    paginate_by: int = 10


class BulkURLSearchView(FormView):
    """
    Bulk search for cases matching URLs
    """

    form_class = BulkURLSearchForm
    template_name: str = "common/bulk_url_search.html"
    success_url: str = reverse_lazy("common:bulk-url-search")

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect:
        """Process contents of valid form"""
        context: dict[str, Any] = self.get_context_data()
        form = context["form"]
        if form.is_valid():
            urls: list[str] = form.cleaned_data["urls"].splitlines()
            bulk_search_results: list[dict] = []
            for url in urls:
                domain: str = extract_domain_from_url(url)
                sanitised_domain: str = sanitise_domain(domain)

                if sanitised_domain:
                    base_cases: QuerySet[BaseCase] = BaseCase.objects.filter(
                        home_page_url__icontains=sanitised_domain
                    )
                    search_term: str = sanitised_domain
                else:
                    base_cases: QuerySet[BaseCase] = BaseCase.objects.filter(
                        home_page_url__icontains=url
                    )
                    search_term: str = url

                bulk_search_results.append(
                    {
                        "search_term": search_term,
                        "found_flag": base_cases.count() > 0,
                        "url": url,
                    }
                )
            return self.render_to_response(
                self.get_context_data(bulk_search_results=bulk_search_results)
            )
        return self.render_to_response()


class ImportCSV(FormView):
    """
    Bulk search for cases matching URLs
    """

    form_class = ImportCSVForm
    template_name: str = "common/import_csv.html"
    success_url: str = reverse_lazy("common:import-csv")

    def post(
        self, request: HttpRequest, *args: tuple[str], **kwargs: dict[str, Any]
    ) -> HttpResponseRedirect:
        context: dict[str, Any] = self.get_context_data()
        form = context["form"]
        if form.is_valid():
            csv_data: str = form.cleaned_data["data"]
            if form.cleaned_data["model"] == "detailed":
                import_detailed_cases_csv(csv_data)
            elif form.cleaned_data["model"] == "mobile":
                import_mobile_cases_csv(csv_data)
        return self.render_to_response(self.get_context_data())
