"""
Test CSV export functions of simplified app
"""

from ...simplified.models import Contact as SimplifiedContact
from ..csv_export import format_simplified_contacts

CONTACTS: list[SimplifiedContact] = [
    SimplifiedContact(
        name="Name 1",
        job_title="Job title 1",
        email="email1",
    ),
    SimplifiedContact(
        name="Name 2",
        job_title="Job title 2",
        email="email2",
    ),
]
EXPECTED_FORMATTED_CONTACTS: str = """Name 1
Job title 1
email1

Name 2
Job title 2
email2
"""


def test_format_contacts():
    """Test that contacts fields values are contatenated"""
    assert format_simplified_contacts(contacts=CONTACTS) == EXPECTED_FORMATTED_CONTACTS
