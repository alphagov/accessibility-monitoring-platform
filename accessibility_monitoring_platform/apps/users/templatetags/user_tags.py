"""
Template tags for users
"""

from django import template
from django.contrib.auth.models import Group, User

register = template.Library()


@register.filter(name="has_group")
def has_group(user: User, group_name: str) -> bool:
    try:
        group: Group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return False
    return True if group in user.groups.all() else False
