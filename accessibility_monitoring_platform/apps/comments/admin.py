from django.contrib import admin

# Register your models here.
from .models import Comments, CommentsHistory


class CommentsAdmin(admin.ModelAdmin):
    """Django admin configuration for Comments model"""

    readonly_fields = ["created_date"]
    search_fields = [
        "case",
        "user",
        "page",
        "body",
        "hidden",
        "endpoint",
        "updated",
    ]
    list_display = [
        "case",
        "user",
        "page",
        "body",
        "hidden",
        "endpoint",
    ]


class CommentsHistoryAdmin(admin.ModelAdmin):
    """Django admin configuration for Comments model"""

    readonly_fields = ["created_date"]
    search_fields = [
        "comment",
        "before",
        "after",
    ]
    list_display = [
        "comment",
        "before",
        "after",
    ]


admin.site.register(Comments, CommentsAdmin)
admin.site.register(CommentsHistory, CommentsHistoryAdmin)
