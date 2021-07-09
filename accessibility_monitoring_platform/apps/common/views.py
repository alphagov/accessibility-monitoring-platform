"""
Common views
"""
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import AMPContactAdminForm


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

    def send_mail(self, cleaned_data):
        subject = cleaned_data.get("subject")
        message = cleaned_data.get("message")
        if subject or message:
            send_mail(
                subject=cleaned_data["subject"],
                message=cleaned_data["message"],
                from_email=self.request.user.email,
                recipient_list=[settings.CONTACT_ADMIN_EMAIL],
            )
