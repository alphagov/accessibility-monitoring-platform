from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from notifications_python_client import NotificationsAPIClient


class NotifyEmailBackend(BaseEmailBackend):
    """ Custom email backend for sending messages using GOV.UK Notify

    https://docs.djangoproject.com/en/3.1/topics/email/#defining-a-custom-email-backend

    Copied from https://github.com/alphagov/digital-buying-guide/blob/master/ictcg/email.py
    """

    _base_url = 'https://api.notifications.service.gov.uk'
    _client_class = NotificationsAPIClient
    _api_key = None
    client = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_key = settings.EMAIL_NOTIFY_API_KEY

    def send_messages(self, email_messages):
        self.client = self._client_class(self._api_key, self._base_url)
        count = 0
        for email_message in email_messages:
            for recipient in email_message.to:
                self.client.send_email_notification(
                    recipient,
                    settings.EMAIL_NOTIFY_BASIC_TEMPLATE,
                    personalisation={
                        'subject': email_message.subject,
                        'body': email_message.body,
                    },
                )
            count += 1
        return count

    def close(self):
        self.client = None
