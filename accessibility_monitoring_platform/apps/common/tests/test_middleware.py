""" test_middleware - Tests for common middleware"""

from django.urls import reverse
import pytest

from ..models import UserCacheUniqueHash


@pytest.mark.django_db
def test_middleware_caches_user_unique_id(client, django_user_model):
    """Tests if middleware caches user id in database"""
    assert UserCacheUniqueHash.objects.all().count() == 0
    user = django_user_model.objects.create_user(username="user1", password="bar")
    client.force_login(user)
    client.get(reverse("dashboard:home"))
    assert UserCacheUniqueHash.objects.all().count() == 1
