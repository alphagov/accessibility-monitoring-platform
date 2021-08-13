"""
Common views
"""
from typing import Any, Dict

from django.conf import settings
from django.core.mail import send_mail
from django.forms.models import ModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import AMPContactAdminForm, AMPIssueReportForm
from .models import IssueReport


class ContactAdminView(FormView):
    """
    Send email to platform admin
    """

    form_class = AMPContactAdminForm
    template_name: str = "common/contact_admin.html"
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        self.send_mail(form.cleaned_data)
        return super().form_valid(form)

    def send_mail(self, cleaned_data: Dict[str, str]) -> None:
        subject = cleaned_data.get("subject")
        message = cleaned_data.get("message")
        if subject or message:
            send_mail(
                subject=subject,
                message=message,
                from_email=self.request.user.email,
                recipient_list=[settings.CONTACT_ADMIN_EMAIL],
            )


class IssueReportView(FormView):
    """
    Save user feedback
    """

    form_class = AMPIssueReportForm
    template_name: str = "common/issue_report.html"
    success_url = reverse_lazy("dashboard:home")

    def get(self, request, *args, **kwargs):
        """Populate form"""
        self.form: AMPIssueReportForm = self.form_class(self.request.GET)
        self.form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add field values into context"""
        context: Dict[str, Any] = super().get_context_data(**kwargs)
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
        subject = f"Platform issue on {issue_report.page_title}"
        message = (
            f"Reported by: {issue_report.created_by}\n\n{issue_report.description}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=self.request.user.email,
            recipient_list=[settings.CONTACT_ADMIN_EMAIL],
        )
