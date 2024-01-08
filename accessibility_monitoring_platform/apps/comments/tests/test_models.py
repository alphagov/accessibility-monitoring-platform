"""
Tests for cases models
"""
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from ...comments.models import Comment
from ..models import Case

DATETIME_COMMENT_UPDATED: datetime = datetime(2021, 9, 26, tzinfo=timezone.utc)


@pytest.mark.django_db
def test_comment_updated_updated():
    """Test the comment updated field is updated"""
    case: Case = Case.objects.create()
    comment: Comment = Comment.objects.create(case=case)

    with patch(
        "django.utils.timezone.now", Mock(return_value=DATETIME_COMMENT_UPDATED)
    ):
        comment.save()

    assert comment.updated == DATETIME_COMMENT_UPDATED
