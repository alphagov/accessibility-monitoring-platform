"""Admin - admin page for comments"""
from django.contrib import admin

from .models import Comment


class CommentAdmin(admin.ModelAdmin):
    """Django admin configuration for Comment model"""

    readonly_fields = ["created_date"]
    search_fields = [
        "case__organisation_name",
        "user__username",
        "body",
        "hidden",
    ]
    list_display = [
        "case",
        "user",
        "body",
        "hidden",
    ]


admin.site.register(Comment, CommentAdmin)
