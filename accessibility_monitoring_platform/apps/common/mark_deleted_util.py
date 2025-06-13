"""Mark object as deleted utility put in its own module to avoid circular imports"""

from django.http import HttpRequest
from django.http.request import QueryDict

from ..simplified.utils import record_simplified_model_update_event


def get_id_from_button_name(
    button_name_prefix: str, querydict: QueryDict
) -> int | None:
    """
    Given a button name in the form: prefix_[id] extract and return the id value.
    """
    key_names: list[str] = [
        key for key in querydict.keys() if key.startswith(button_name_prefix)
    ]
    object_id: int | None = None
    if len(key_names) == 1:
        id_string: str = key_names[0].replace(button_name_prefix, "")
        object_id: int | None = int(id_string) if id_string.isdigit() else None
    return object_id


def mark_object_as_deleted(
    request: HttpRequest, delete_button_prefix: str, object_to_delete_model
) -> None:
    """
    Check for delete/remove button in request. Mark object as deleted.
    """
    object_id_to_delete: int | None = get_id_from_button_name(
        button_name_prefix=delete_button_prefix,
        querydict=request.POST,
    )
    if object_id_to_delete is not None:
        object_to_delete = object_to_delete_model.objects.get(id=object_id_to_delete)
        object_to_delete.is_deleted = True
        record_simplified_model_update_event(
            user=request.user, model_object=object_to_delete
        )
        object_to_delete.save()
