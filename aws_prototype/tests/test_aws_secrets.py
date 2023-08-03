import pytest

from typing import Dict
from unittest.mock import patch, MagicMock

from ..aws_secrets import get_notify_secret

NOTIFY_SECRET_STR: str = """{"EMAIL_NOTIFY_API_KEY": "test_env__amp-random","EMAIL_NOTIFY_BASIC_TEMPLATE": "random"}"""
NOTIFY_SECRET: Dict[str, str] = {
    "EMAIL_NOTIFY_API_KEY": "test_env__amp-random",
    "EMAIL_NOTIFY_BASIC_TEMPLATE": "random",
}


def test_get_notify_secret():
    with patch("aws_prototype.aws_secrets.boto3") as mock_boto3:
        mock_client: MagicMock = MagicMock(name="mock_client")
        mock_client.get_secret_value.return_value = {"SecretString": NOTIFY_SECRET_STR}
        mock_returned_session: MagicMock = MagicMock(name="mock_returned_session")
        mock_returned_session.client.return_value = mock_client
        mock_session: MagicMock = MagicMock(name="mock_session")
        mock_session.return_value = mock_returned_session
        mock_boto3.session.Session = mock_session

        assert get_notify_secret() == NOTIFY_SECRET
