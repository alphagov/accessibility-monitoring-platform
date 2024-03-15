"""Admin - admin page for comments"""

from django.contrib import admin

from .models import Alert, Comment


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


class AlertAdmin(admin.ModelAdmin):
    """Django admin configuration for Alert model"""

    readonly_fields = ["created", "comment"]
    search_fields = [
        "case__organisation_name",
        "case__id",
        "target_user__username",
        "message",
    ]
    list_display = [
        "case",
        "target_user",
        "type",
        "due_date",
        "message",
        "read",
        "is_deleted",
    ]
    list_filter = [
        "type",
        "read",
        "is_deleted",
        ("target_user", admin.RelatedOnlyFieldListFilter),
    ]
    show_facets = admin.ShowFacets.ALWAYS


admin.site.register(Comment, CommentAdmin)
admin.site.register(Alert, AlertAdmin)
