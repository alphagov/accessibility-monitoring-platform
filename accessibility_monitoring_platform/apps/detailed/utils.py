"""
Utils for detailed Case app
"""

import copy
import json
from typing import Any

from django.contrib.auth.models import User
from django.db import models

from ..common.utils import diff_model_fields
from .models import DetailedCase, DetailedCaseHistory, EventHistory


def record_model_create_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    EventHistory.objects.create(
        detailed_case=detailed_case,
        created_by=user,
        parent=model_object,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_model_update_event(
    user: User, model_object: models.Model, detailed_case: DetailedCase
) -> None:
    """Record model update event"""
    previous_object = model_object.__class__.objects.get(pk=model_object.id)
    previous_object_fields = copy.copy(vars(previous_object))
    del previous_object_fields["_state"]
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    diff_fields: dict[str, Any] = diff_model_fields(
        old_fields=previous_object_fields, new_fields=model_object_fields
    )
    if diff_fields:
        EventHistory.objects.create(
            detailed_case=detailed_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )


def add_to_detailed_case_history(
    detailed_case: DetailedCase,
    user: User,
    value: str,
    event_type: DetailedCaseHistory.EventType = DetailedCaseHistory.EventType.NOTE,
) -> None:
    """Add latest change of DetailedCase.status to history"""
    DetailedCaseHistory.objects.create(
        detailed_case=detailed_case,
        event_type=event_type,
        created_by=user,
        value=value,
    )
