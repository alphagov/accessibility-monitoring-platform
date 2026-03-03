"""Record case model events"""

from django.contrib.auth.models import User
from django.db import models

from ..detailed.utils import (
    record_detailed_model_create_event,
    record_detailed_model_update_event,
)
from ..mobile.utils import (
    record_mobile_model_create_event,
    record_mobile_model_update_event,
)
from ..simplified.utils import (
    record_simplified_model_create_event,
    record_simplified_model_update_event,
)
from .models import BaseCase


def record_create_event(
    user: User, model_object: models.Model, base_case: BaseCase
) -> None:
    """Record model create event"""
    if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
        record_simplified_model_create_event(
            user=user, model_object=model_object, simplified_case=base_case.get_case()
        )
    elif base_case.test_type == BaseCase.TestType.DETAILED:
        record_detailed_model_create_event(
            user=user, model_object=model_object, detailed_case=base_case.get_case()
        )
    else:
        record_mobile_model_create_event(
            user=user, model_object=model_object, mobile_case=base_case.get_case()
        )


def record_update_event(
    user: User, model_object: models.Model, base_case: BaseCase
) -> None:
    """Record model update event"""
    if base_case.test_type == BaseCase.TestType.SIMPLIFIED:
        record_simplified_model_update_event(
            user=user, model_object=model_object, simplified_case=base_case.get_case()
        )
    elif base_case.test_type == BaseCase.TestType.DETAILED:
        record_detailed_model_update_event(
            user=user, model_object=model_object, detailed_case=base_case.get_case()
        )
    else:
        record_mobile_model_update_event(
            user=user, model_object=model_object, mobile_case=base_case.get_case()
        )
