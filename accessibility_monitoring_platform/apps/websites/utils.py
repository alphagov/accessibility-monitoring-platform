"""
Utility functions for websites app
"""

from django.db.models import Q, QuerySet

from .models import NutsConversion



def get_list_of_nuts318_codes(location: str) -> QuerySet[NutsConversion]:
    """
    Filters town or city and returns a list of nuts318 area codes for filtering websites.
    Args:
        location (str): The string to search
    Returns:
        List(str): A list of nuts318 codes
    """

    nuts_codes: QuerySet[NutsConversion] = (
        NutsConversion.objects.using("pubsecweb_db")
        .filter(
            Q(lad18nm__icontains=location)
            | Q(lau118nm__icontains=location)
            | Q(nuts318nm__icontains=location)
            | Q(nuts218nm__icontains=location)
        )
        .values_list("nuts318cd", flat=True)
        .distinct()
    )

    return nuts_codes