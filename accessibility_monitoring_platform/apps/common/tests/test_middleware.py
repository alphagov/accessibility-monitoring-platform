""" test_middleware - Tests for common middleware"""
import pytest
from unittest.mock import patch, Mock

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.urls import reverse

from ..models import UserCacheUniqueHash
from ..middleware.validate_host_middleware import ValidateHostMiddleware


@pytest.mark.django_db
def test_middleware_caches_user_unique_id(client, django_user_model):
    """Tests if middleware caches user id in database"""
    assert UserCacheUniqueHash.objects.all().count() == 0
    user = django_user_model.objects.create_user(username="user1", password="bar")
    client.force_login(user)
    client.get(reverse("dashboard:home"))
    assert UserCacheUniqueHash.objects.all().count() == 1


@patch(
    "accessibility_monitoring_platform.apps.common.middleware.validate_host_middleware.logger.info"
)
def test_validate_host_middleware_valid_host(mock_logger):
    """Tests host validation for valid host"""
    host: str = settings.ALLOWED_HOSTS[0]
    mock_request = Mock()
    mock_request._get_raw_host.return_value = host
    validate_host_middleware = ValidateHostMiddleware(Mock())
    validate_host_middleware(mock_request)

    mock_logger.assert_called_once_with("Valid host found: %s", host)


@pytest.mark.parametrize(
    "host",
    [
        "10.0.1.2",
        "10.0.3.4",
        "10.0.0.122:8001",
    ],
)
@patch(
    "accessibility_monitoring_platform.apps.common.middleware.validate_host_middleware.logger.info"
)
def test_validate_host_middleware_valid_host_ip(mock_logger, host):
    """Tests host validation for valid host IP"""
    mock_request = Mock()
    mock_request._get_raw_host.return_value = host
    validate_host_middleware = ValidateHostMiddleware(Mock())
    validate_host_middleware(mock_request)

    mock_logger.assert_called_once_with("Valid host found: %s", host)


def test_validate_host_middleware_invalid_host():
    """Tests host validation for invalid host"""
    host: str = "invalid.com"
    mock_request = Mock()
    mock_request._get_raw_host.return_value = host
    validate_host_middleware = ValidateHostMiddleware(Mock())

    with pytest.raises(DisallowedHost) as excinfo:
        validate_host_middleware(mock_request)

    assert f"Unexpected host in request: {host}" in str(excinfo.value)
