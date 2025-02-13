"""
Common views
"""

import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.mail import EmailMessage
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView
from django.views.generic.list import ListView

from ..cases.models import Case
from ..common.sitemap import PlatformPage, Sitemap
from .email_template_utils import get_email_template_context
from .forms import (
    ActiveQAAuditorUpdateForm,
    AMPContactAdminForm,
    AMPIssueReportForm,
    BulkURLSearchForm,
    EmailTemplateCreateUpdateForm,
    FooterLinkFormset,
    FooterLinkOneExtraFormset,
    FrequentlyUsedLinkFormset,
    FrequentlyUsedLinkOneExtraFormset,
    PlatformCheckingForm,
)
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
    EmailTemplate,
    Event,
    FooterLink,
    FrequentlyUsedLink,
    IssueReport,
    Platform,
)
from .platform_template_view import PlatformTemplateView
from .utils import (
    extract_domain_from_url,
    get_one_year_ago,
    get_platform_settings,
    mark_object_as_deleted,
    record_model_create_event,
    record_model_update_event,
    sanitise_domain,
)

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE_PREVIEW_CASE_ID: int = 1170


class NextPlatformPageMixin:
    """Mixin for UpdateViews with Save and continue buttons"""

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
                    record_model_create_event(user=self.request.user, model_object=link)
                else:
                    record_model_update_event(user=self.request.user, model_object=link)
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
                    record_model_create_event(user=self.request.user, model_object=link)
                else:
                    record_model_update_event(user=self.request.user, model_object=link)
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
    template_name: str = "common/platform_checking.html"
    success_url: str = reverse_lazy("common:platform-checking")

    def test_func(self):
        """Only staff users have access to this view"""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get context data for template rendering"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        number_of_old_events: int = Event.objects.filter(
            created__lte=get_one_year_ago()
        ).count()
        context["number_of_old_events"] = number_of_old_events
        return context

    def form_valid(self, form):
        if "delete_old_events" in self.request.POST:
            one_year_ago: datetime = get_one_year_ago()
            number_of_old_events: int = Event.objects.filter(
                created__lte=one_year_ago
            ).count()
            Event.objects.filter(created__lte=one_year_ago).delete()
            logger.warning(
                "%s deleted %d old events",
                self.request.user.email,
                number_of_old_events,
            )
            return super().form_valid(form)
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
                    cases: QuerySet[Case] = Case.objects.filter(
                        home_page_url__icontains=sanitised_domain
                    )
                    search_term: str = sanitised_domain
                else:
                    cases: QuerySet[Case] = Case.objects.filter(
                        home_page_url__icontains=url
                    )
                    search_term: str = url

                bulk_search_results.append(
                    {
                        "search_term": search_term,
                        "found_flag": cases.count() > 0,
                        "url": url,
                    }
                )
            return self.render_to_response(
                self.get_context_data(bulk_search_results=bulk_search_results)
            )
        return self.render_to_response()


class EmailTemplateListView(ListView):
    """
    View of list of email templates.
    """

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "common/emails/template_list.html"
    context_object_name: str = "email_templates"
    paginate_by: int = 10

    def get_queryset(self) -> QuerySet[EmailTemplate]:
        return EmailTemplate.objects.filter(type=EmailTemplate.Type.SIMPLE).filter(
            is_deleted=False
        )


class EmailTemplatePreviewDetailView(DetailView):
    """
    View preview of email template
    """

    model: type[EmailTemplate] = EmailTemplate
    template_name: str = "common/emails/template_preview.html"
    context_object_name: str = "email_template"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add case and email template to context"""
        context: dict[str, Any] = super().get_context_data(**kwargs)
        case: Case = Case.objects.filter(pk=EMAIL_TEMPLATE_PREVIEW_CASE_ID).first()
        if case is not None:
            email_template_context: dict[str, Any] = get_email_template_context(
                case=case
            )
            context["email_template_render"] = self.object.render(
                context=email_template_context
            )
        return context


class EmailTemplateCreateView(CreateView):
    """
    View to create email template
    """

    model: type[EmailTemplate] = EmailTemplate
    form_class: type[EmailTemplateCreateUpdateForm] = EmailTemplateCreateUpdateForm
    template_name: str = "common/emails/template_create.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        email_template: EmailTemplate = form.save(commit=False)
        email_template.created_by = self.request.user
        email_template.updated_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        record_model_create_event(user=self.request.user, model_object=self.object)
        if "save_preview" in self.request.POST:
            return reverse_lazy(
                "common:email-template-preview", kwargs={"pk": self.object.id}
            )
        return reverse_lazy(
            "common:email-template-update", kwargs={"pk": self.object.id}
        )


class EmailTemplateUpdateView(UpdateView):
    """
    View to update email template
    """

    model: type[EmailTemplate] = EmailTemplate
    context_object_name: str = "email_template"
    form_class: type[EmailTemplateCreateUpdateForm] = EmailTemplateCreateUpdateForm
    template_name: str = "common/emails/template_update.html"

    def form_valid(self, form: ModelForm):
        """Process contents of valid form"""
        email_template: EmailTemplate = form.save(commit=False)
        email_template.updated_by = self.request.user
        record_model_update_event(user=self.request.user, model_object=email_template)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Remain on current page on save"""
        if "save_preview" in self.request.POST:
            return reverse_lazy(
                "common:email-template-preview", kwargs={"pk": self.object.id}
            )
        return self.request.path
