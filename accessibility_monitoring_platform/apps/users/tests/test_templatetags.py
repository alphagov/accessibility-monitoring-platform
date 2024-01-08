"""
Tests for users templatetags
"""
import pytest
from django.contrib.auth.models import Group, User

from ..templatetags.user_tags import has_group

GROUP_NAME = "Magic circle"


@pytest.mark.django_db
def test_has_group_returns_true():
    """Returns boolean true if user in group"""
    user: User = User.objects.create()
    group: Group = Group.objects.create(name=GROUP_NAME)
    group.user_set.add(user)

    assert has_group(user=user, group_name=GROUP_NAME)


@pytest.mark.django_db
def test_has_group_returns_false():
    """Returns boolean false if user not in group"""
    user: User = User.objects.create()
    Group.objects.create(name=GROUP_NAME)

    assert not has_group(user=user, group_name=GROUP_NAME)
