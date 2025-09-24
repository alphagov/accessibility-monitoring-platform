"""
Utils for mobile Case app
"""

import copy
import json
from typing import Any

from django.contrib.auth.models import User
from django.db import models

from ..common.utils import diff_model_fields
from .models import EventHistory, MobileCase


def record_mobile_model_create_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
) -> None:
    """Record model create event"""
    model_object_fields = copy.copy(vars(model_object))
    del model_object_fields["_state"]
    EventHistory.objects.create(
        mobile_case=mobile_case,
        created_by=user,
        parent=model_object,
        event_type=EventHistory.Type.CREATE,
        difference=json.dumps(model_object_fields, default=str),
    )


def record_mobile_model_update_event(
    user: User, model_object: models.Model, mobile_case: MobileCase
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
            mobile_case=mobile_case,
            created_by=user,
            parent=model_object,
            difference=json.dumps(diff_fields, default=str),
        )
