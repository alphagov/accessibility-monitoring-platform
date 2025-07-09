"""
Forms - cases
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet

from ..cases.models import (
    ALL_CASE_STATUS_CHOICES,
    CASE_STATUS_UNKNOWN,
    BaseCase,
    Complaint,
    Sort,
)
from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceField,
    AMPDateField,
    AMPDateRangeForm,
    AMPModelChoiceField,
)
from ..common.models import Sector, SubCategory

TEST_TYPE_CHOICES: list[tuple[str, str]] = [("", "All")] + BaseCase.TestType.choices
ENFORCEMENT_BODY_FILTER_CHOICES = [("", "All")] + BaseCase.EnforcementBody.choices
STATUS_CHOICES: list[tuple[str, str]] = [("", "All")] + [
    choice
    for choice in ALL_CASE_STATUS_CHOICES
    if choice[0] != CASE_STATUS_UNKNOWN.value
]
RECOMMENDATION_CHOICES: list[tuple[str, str]] = [
    ("", "All")
] + BaseCase.RecommendationForEnforcement.choices


class DateType(models.TextChoices):
    TEST_START = (
        "simplifiedcase__audit_simplifiedcase__date_of_test",
        "Date test started",
    )
    SENT = "simplifiedcase__sent_to_enforcement_body_sent_date", "Date sent to EB"
    UPDATED = "updated_date", "Case updated"


def get_search_user_choices(user_query: QuerySet[User]) -> list[tuple[str, str]]:
    """Return a list of user ids and names, with an additional none option, for use in search"""
    user_choices_with_none: list[tuple[str, str]] = [
        ("", "-----"),
        ("none", "Unassigned"),
    ]
    for user in user_query.order_by("first_name", "last_name"):
        user_choices_with_none.append((user.id, user.get_full_name()))
    return user_choices_with_none


class CaseSearchForm(AMPDateRangeForm):
    """Form for searching for cases"""

    sort_by = AMPChoiceField(label="Sort by", choices=Sort.choices)
    case_search = AMPCharFieldWide(label="Search")
    auditor = AMPChoiceField(label="Auditor")
    reviewer = AMPChoiceField(label="QA Auditor")
    status = AMPChoiceField(label="Status", choices=STATUS_CHOICES)
    recommendation_for_enforcement = AMPChoiceField(
        label="Equality body recommendation", choices=RECOMMENDATION_CHOICES
    )
    date_type = AMPChoiceField(label="Date filter", choices=DateType.choices)
    date_start = AMPDateField(label="Date start")
    date_end = AMPDateField(label="Date end")
    sector = AMPModelChoiceField(label="Sector", queryset=Sector.objects.all())
    is_complaint = AMPChoiceField(label="Filter complaints", choices=Complaint.choices)
    enforcement_body = AMPChoiceField(
        label="Enforcement body", choices=ENFORCEMENT_BODY_FILTER_CHOICES
    )
    subcategory = AMPModelChoiceField(
        label="Sub-category", queryset=SubCategory.objects.all()
    )
    test_type = AMPChoiceField(label="Testing type", choices=TEST_TYPE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        auditor_choices: list[tuple[str, str]] = get_search_user_choices(
            User.objects.filter(groups__name="Historic auditor")
        )
        self.fields["auditor"].choices = auditor_choices
        self.fields["reviewer"].choices = auditor_choices
