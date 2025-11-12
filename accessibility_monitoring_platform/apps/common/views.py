"""
Common views
"""

import logging
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import BaseCase
from ..common.sitemap import PlatformPage, Sitemap
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from .forms import (
    ActiveQAAuditorUpdateForm,
    AMPContactAdminForm,
    BulkURLSearchForm,
    FooterLinkFormset,
    FooterLinkOneExtraFormset,
    FrequentlyUsedLinkFormset,
    FrequentlyUsedLinkOneExtraFormset,
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
from .models import ChangeToPlatform, FooterLink, FrequentlyUsedLink, Platform
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
