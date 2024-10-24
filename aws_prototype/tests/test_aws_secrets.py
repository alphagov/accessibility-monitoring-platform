import json
from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from ..aws_secrets import get_notify_secret

NOTIFY_SECRET: dict[str, str] = {
    "EMAIL_NOTIFY_API_KEY": "test_env__amp-random",
    "EMAIL_NOTIFY_BASIC_TEMPLATE": "blahblah",
}
NOTIFY_SECRET_STR: str = json.dumps(NOTIFY_SECRET)


@pytest.fixture
def secretmanager_client():
    """AWS client for use with stubber"""
    return boto3.client("secretsmanager", region_name="eu-west-2")


@patch("aws_prototype.aws_secrets.boto3.session.Session")
def test_get_notify_secret_returns_secret(mock_session, secretmanager_client):
    """Test get_notify_secret returns secret."""
    stubber: Stubber = Stubber(secretmanager_client)
    stubber.add_response("get_secret_value", {"SecretString": NOTIFY_SECRET_STR})
    stubber.activate()

    mock_returned_session: Mock = Mock()
    mock_returned_session.client.return_value = secretmanager_client
    mock_session.return_value = mock_returned_session

    assert get_notify_secret() == NOTIFY_SECRET


@patch("aws_prototype.aws_secrets.boto3.session.Session")
def test_get_notify_secret_raises_exception(mock_session, secretmanager_client):
    """Test get_notify_secret raises exception."""
    stubber: Stubber = Stubber(secretmanager_client)
    stubber.add_client_error("get_secret_value", "ClientError")
    stubber.activate()

    mock_returned_session: Mock = Mock()
    mock_returned_session.client.return_value = secretmanager_client
    mock_session.return_value = mock_returned_session

    with pytest.raises(ClientError):
        get_notify_secret()
