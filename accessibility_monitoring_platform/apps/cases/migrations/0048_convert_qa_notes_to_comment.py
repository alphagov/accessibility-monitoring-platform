# Generated by Django 4.1.4 on 2023-02-24 09:40

import json
from typing import Dict

from django.core import serializers
from django.db import migrations

EVENT_TYPE_MODEL_CREATE: str = "model_create"
COMMENT_PREFIX: str = "QA NOTES CONVERTED TO COMMENT\n\n"


def convert_qa_notes_to_comments(
    apps, schema_editor
):  # pylint: disable=unused-argument
    """Convert reviewer notes on case into comment"""
    Case = apps.get_model("cases", "Case")
    if Case.objects.all().count() == 0:
        # This process goes haywire when db is empty (e.g. setting up test env)
        return
    Comment = apps.get_model("comments", "Comment")
    Event = apps.get_model("common", "Event")
    ContentType = apps.get_model("contenttypes", "contenttype")
    comment_contenttype = ContentType.objects.get(app_label="comments", model="comment")
    comment_contenttype_id = comment_contenttype.id

    for case in Case.objects.exclude(reviewer_notes=""):
        comment = Comment.objects.create(
            case=case,
            user=case.auditor,
            body=f"{COMMENT_PREFIX}{case.reviewer_notes}",
        )

        value: Dict[str, str] = {}
        value["new"] = serializers.serialize("json", [comment])
        Event.objects.create(
            created_by=case.auditor,
            content_type_id=comment_contenttype_id,
            object_id=comment.id,
            value=json.dumps(value),
            type=EVENT_TYPE_MODEL_CREATE,
        )


def convert_comments_to_qa_notes(
    apps, schema_editor
):  # pylint: disable=unused-argument
    """Convert comments created above back into review notes on case"""
    Event = apps.get_model("common", "Event")
    Comment = apps.get_model("comments", "Comment")
    ContentType = apps.get_model("contenttypes", "contenttype")
    comment_contenttype = ContentType.objects.get(app_label="comments", model="comment")
    comment_contenttype_id = comment_contenttype.id

    for event in Event.objects.filter(
        content_type_id=comment_contenttype_id, type=EVENT_TYPE_MODEL_CREATE
    ):
        comment = Comment.objects.get(id=event.object_id)
        case = comment.case
        if comment.body.find(COMMENT_PREFIX) > -1:
            case.reviewer_notes = comment.body.replace(COMMENT_PREFIX, "")
            case.save()
        event.delete()
        comment.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0047_alter_case_qa_status"),
        ("comments", "0008_delete_commenthistory"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(
            convert_qa_notes_to_comments, reverse_code=convert_comments_to_qa_notes
        ),
    ]
