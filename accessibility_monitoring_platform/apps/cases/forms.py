"""Forms - cases"""

import requests
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet

from ..cases.models import (
    ALL_CASE_STATUS_SEARCH_CHOICES,
    CASE_STATUS_UNKNOWN,
    BaseCase,
    Complaint,
    Sort,
    extract_id_from_case_url,
)
from ..common.forms import (
    AMPCharFieldWide,
    AMPChoiceField,
    AMPDateField,
    AMPDateRangeForm,
    AMPIntegerField,
    AMPModelChoiceField,
    AMPURLField,
)
from ..common.models import Sector, SubCategory

TEST_TYPE_CHOICES: list[tuple[str, str]] = [("", "All")] + BaseCase.TestType.choices
ENFORCEMENT_BODY_FILTER_CHOICES = [("", "All")] + BaseCase.EnforcementBody.choices
STATUS_CHOICES: list[tuple[str, str]] = [("", "All")] + [
    choice
    for choice in ALL_CASE_STATUS_SEARCH_CHOICES
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

    test_type = AMPChoiceField(label="Testing type", choices=TEST_TYPE_CHOICES)
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
    case_number = AMPIntegerField(label="Case number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        auditor_choices: list[tuple[str, str]] = get_search_user_choices(
            User.objects.filter(groups__name="Historic auditor")
        )
        self.fields["auditor"].choices = auditor_choices
        self.fields["reviewer"].choices = auditor_choices


class PreviousCaseURLForm(forms.ModelForm):
    """Form for a case with a previous URL field"""

    previous_case_url = AMPURLField(
        label="URL to previous case · Included in export",
        help_text="If the website has been previously audited, include a link to the case below",
    )

    class Meta:
        model = BaseCase
        fields = [
            "previous_case_url",
        ]

    def clean_previous_case_url(self):
        """Check url contains case number"""
        previous_case_url = self.cleaned_data.get("previous_case_url")

        # Check if URL was entered
        if not previous_case_url:
            return previous_case_url

        if requests.head(previous_case_url, timeout=10).status_code >= 400:
            raise ValidationError("Previous case URL does not exist")

        try:
            case_id: int | None = extract_id_from_case_url(case_url=previous_case_url)
        except AttributeError:
            raise ValidationError(  # pylint: disable=raise-missing-from
                "Previous case URL did not contain case id"
            )

        # Check if Case exists matching id from URL
        if case_id and BaseCase.objects.filter(id=case_id).exists():
            return previous_case_url
        else:
            raise ValidationError("Previous case not found in platform")
