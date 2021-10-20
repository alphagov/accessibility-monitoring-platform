"""
Tests for templatetags
"""

from django.contrib.auth.models import Group, User
from django.test import TestCase

from ..templatetags.user_tags import has_group

GROUP_NAME = "Magic circle"


class EmailInclusionListTestCase(TestCase):
    """
    Test has_group templatetag

    Methods
    -------
    test_has_group_returns_true()
        Returns boolean true if user in group
    test_has_group_returns_false()
        Returns boolean false if user not in group
    """

    def test_has_group_returns_true(self):
        """ Returns boolean true if user in group """
        user: User = User.objects.create()
        group: Group = Group.objects.create(name=GROUP_NAME)
        group.user_set.add(user)
        self.assertEqual(has_group(user=user, group_name=GROUP_NAME), True)

    def test_has_group_returns_false(self):
        """ Returns boolean false if user not in group """
        user: User = User.objects.create()
        Group.objects.create(name=GROUP_NAME)
        self.assertEqual(has_group(user=user, group_name=GROUP_NAME), False)
