""" test_middleware - Tests for common middleware"""

from unittest.mock import Mock

import pytest
from django.urls import reverse

from ..middleware.healthcheck_middleware import HealthcheckMiddleware
from ..models import UserCacheUniqueHash


@pytest.mark.django_db
def test_middleware_caches_user_unique_id(client, django_user_model):
    """Tests if middleware caches user id in database"""
    assert UserCacheUniqueHash.objects.all().count() == 0
    user = django_user_model.objects.create_user(username="user1", password="bar")
    client.force_login(user)
    client.get(reverse("dashboard:home"))
    assert UserCacheUniqueHash.objects.all().count() == 1


def test_healthcheck_middleware_healthcheck_request():
    """Tests healthcheck requests don't call get_response"""
    mock_request = Mock()
    mock_request.META = {"PATH_INFO": "/healthcheck/"}
    mock_get_response = Mock()
    healthcheck_middleware = HealthcheckMiddleware(Mock())
    healthcheck_middleware.get_response = mock_get_response
    healthcheck_middleware(mock_request)

    mock_get_response.assert_not_called()


def test_healthcheck_middleware_non_healthcheck_request():
    """Tests non-healthcheck requests call get_response"""
    mock_request = Mock()
    mock_request.META = {"PATH_INFO": "/other/"}
    mock_get_response = Mock()
    healthcheck_middleware = HealthcheckMiddleware(Mock())
    healthcheck_middleware.get_response = mock_get_response
    healthcheck_middleware(mock_request)

    mock_get_response.assert_called_once()
