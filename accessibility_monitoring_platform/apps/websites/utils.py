"""
Utility functions for websites app
"""

from django.db.models import QuerySet
from .models import NutsConversion

from typing import (
    Any,
    List,
)


def get_list_of_nuts118(location: str) -> Any:
    """Filters town or city and returns a list of nuts118 area codes for filtering websites

    Args:
        location (str): The string to search

    Returns:
        Any: A list of nuts118 codes
    """
    lad18: QuerySet = NutsConversion.objects.using("pubsecweb_db").filter(
        lad18nm__icontains=location
    )

    lau118: QuerySet = NutsConversion.objects.using("pubsecweb_db").filter(
        lau118nm__icontains=location
    )

    nuts318: QuerySet = NutsConversion.objects.using("pubsecweb_db").filter(
        nuts318nm__icontains=location
    )

    nuts218: QuerySet = NutsConversion.objects.using("pubsecweb_db").filter(
        nuts218nm__icontains=location
    )

    nuts_code: QuerySet = lad18 | lau118 | nuts318 | nuts218

    list_of_nuts118: List[Any] = [x["nuts318cd"] for x in nuts_code.values()]
    unique_nuts118: List[str] = list(set(list_of_nuts118))
    return unique_nuts118
