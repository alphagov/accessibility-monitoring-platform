"""
Test utility functions of cases app
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User

from ...audits.models import Audit
from ...common.models import Boolean, Sector, SubCategory
from ...mobile.models import MobileCase
from ...simplified.models import CaseStatus, SimplifiedCase
from ..forms import DateType
from ..models import BaseCase, Sort
from ..utils import filter_cases, find_duplicate_cases

ORGANISATION_NAME: str = "Organisation name one"
ORGANISATION_NAME_COMPLAINT: str = "Organisation name two"
ORGANISATION_NAME_ECNI: str = "Organisation name ecni"
ORGANISATION_NAME_EHRC: str = "Organisation name ehrc"
ORGANISATION_NAME_NO_FURTHER_ACTION: str = "Organisation name no further action"
ORGANISATION_NAME_FOR_ENFORCEMENT: str = "Organisation name for enforcement"
ORGANISATION_NAME_NOT_SELECTED: str = "Organisation name not selected"
HOME_PAGE_URL: str = "https://example.com"
PSB_LOCATION: str = "England"
SECTOR_NAME: str = "Sector name"
PARENTAL_ORGANISATION_NAME: str = "Parent organisation"
WEBSITE_NAME: str = "Website name"
SUBCATEGORY_NAME: str = "Sub-category name"
CASE_IDENTIFIER: str = "#M-1"
APP_NAME: str = "App name"
APP_STORE_URL: str = "https://appstore.com"
CASE_NUMBER: int = 99

PAST_DATE: date = date(1900, 1, 1)
TODAYS_DATE: date = date.today()

DOMAIN: str = "domain.com"
HOME_PAGE_URL: str = f"https://{DOMAIN}"
ORGANISATION_NAME: str = "Organisation name"


@dataclass
class MockCase:
    """Mock of case for testing"""

    sent_date: str


@dataclass
class MockForm:
    """Mock of form for testing"""

    cleaned_data: dict[str, str]


@pytest.mark.django_db
def test_case_filtered_by_date_of_test_date_range():
    """Test searching for cases by date of test in date range."""
    excluded_simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name="Excluded"
    )
    Audit.objects.create(
        simplified_case=excluded_simplified_case, date_of_test=PAST_DATE
    )
    included_simplified_case: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name="Included"
    )
    Audit.objects.create(
        simplified_case=included_simplified_case, date_of_test=TODAYS_DATE
    )

    form: MockForm = MockForm(
        cleaned_data={
            "date_type": DateType.TEST_START,
            "date_start": TODAYS_DATE,
            "date_end": TODAYS_DATE,
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == "Included"


@pytest.mark.django_db
def test_case_filtered_by_sent_to_enforcement_body_date_range():
    """Test searching for cases by sent to enforcement body date range"""
    SimplifiedCase.objects.create(
        organisation_name="Excluded", sent_to_enforcement_body_sent_date=PAST_DATE
    )
    SimplifiedCase.objects.create(
        organisation_name="Included", sent_to_enforcement_body_sent_date=TODAYS_DATE
    )

    form: MockForm = MockForm(
        cleaned_data={
            "date_type": DateType.SENT,
            "date_start": TODAYS_DATE,
            "date_end": TODAYS_DATE,
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == "Included"


@pytest.mark.django_db
def test_case_filtered_by_updated_date_range():
    """Test searching for cases by updated date range"""
    with patch(
        "django.utils.timezone.now",
        Mock(
            return_value=datetime(
                PAST_DATE.year, PAST_DATE.month, PAST_DATE.day, tzinfo=timezone.utc
            )
        ),
    ):
        SimplifiedCase.objects.create(organisation_name="Excluded")
    with patch(
        "django.utils.timezone.now",
        Mock(
            return_value=datetime(
                TODAYS_DATE.year,
                TODAYS_DATE.month,
                TODAYS_DATE.day,
                tzinfo=timezone.utc,
            )
        ),
    ):
        SimplifiedCase.objects.create(organisation_name="Included")

    form: MockForm = MockForm(
        cleaned_data={
            "date_type": DateType.UPDATED,
            "date_start": TODAYS_DATE,
            "date_end": TODAYS_DATE,
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == "Included"


@pytest.mark.django_db
def test_filtering_by_date_range_is_inclusive():
    """Test filtering Cases by date range includes Cases with matching dates"""
    with patch(
        "django.utils.timezone.now",
        Mock(
            return_value=datetime(
                TODAYS_DATE.year,
                TODAYS_DATE.month,
                TODAYS_DATE.day,
                tzinfo=timezone.utc,
            )
        ),
    ):
        SimplifiedCase.objects.create()

    form: MockForm = MockForm(
        cleaned_data={
            "date_type": DateType.UPDATED,
            "date_end": TODAYS_DATE,
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1

    form: MockForm = MockForm(
        cleaned_data={
            "date_type": DateType.UPDATED,
            "date_end": TODAYS_DATE,
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.django_db
def test_case_filtered_by_auditor():
    """Test that filtering cases by auditor is reflected in the queryset"""
    auditor: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    SimplifiedCase.objects.create(auditor=auditor)
    form: MockForm = MockForm(cleaned_data={"auditor": auditor.id})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.django_db
def test_case_filtered_by_reviewer():
    """Test that filtering cases by reviewer is reflected in the queryset"""
    reviewer: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    SimplifiedCase.objects.create(reviewer=reviewer)
    form: MockForm = MockForm(cleaned_data={"reviewer": reviewer.id})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.django_db
def test_case_filtered_by_case_number():
    """Test that searching for case by number is reflected in the queryset"""
    SimplifiedCase.objects.create(case_number=CASE_NUMBER)
    form: MockForm = MockForm(cleaned_data={"case_number": str(CASE_NUMBER)})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].case_number == CASE_NUMBER


@pytest.mark.django_db
def test_case_filtered_by_case_identifier():
    """Test that filtering cases by case identifier is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name="Found")
    case_not_found: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name="Not Found"
    )
    case_not_found.case_identifier = "#S-10"
    form: MockForm = MockForm(cleaned_data={"case_search": "s-1"})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == "Found"


@pytest.mark.django_db
def test_case_filtered_by_status():
    """Test that filtering cases by status is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)
    form: MockForm = MockForm(cleaned_data={"status": SimplifiedCase.Status.UNASSIGNED})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_case_filtered_by_case_number_search_string():
    """Test that searching for case by number is reflected in the queryset"""
    SimplifiedCase.objects.create(case_number=CASE_NUMBER)
    form: MockForm = MockForm(cleaned_data={"case_search": str(CASE_NUMBER)})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].case_number == CASE_NUMBER


@pytest.mark.parametrize(
    "search_string",
    [
        ORGANISATION_NAME,
        HOME_PAGE_URL,
        PSB_LOCATION,
        SECTOR_NAME,
        PARENTAL_ORGANISATION_NAME,
        WEBSITE_NAME,
        SUBCATEGORY_NAME,
        CASE_IDENTIFIER,
        APP_NAME,
        APP_STORE_URL,
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_search_string(search_string):
    """Test that searching for cases is reflected in the queryset"""
    sector: Sector = Sector.objects.create(name=SECTOR_NAME)
    subcategory: SubCategory = SubCategory.objects.create(name=SUBCATEGORY_NAME)
    MobileCase.objects.create(
        organisation_name=ORGANISATION_NAME,
        home_page_url=HOME_PAGE_URL,
        psb_location=PSB_LOCATION,
        sector=sector,
        parental_organisation_name=PARENTAL_ORGANISATION_NAME,
        website_name=WEBSITE_NAME,
        subcategory=subcategory,
        app_name=APP_NAME,
        app_store_url=APP_STORE_URL,
    )
    form: MockForm = MockForm(cleaned_data={"case_search": search_string})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.django_db
def test_simplified_case_filtered_by_ready_to_qa():
    """Test that case with status Ready to QA is found"""
    SimplifiedCase.objects.create(
        status=SimplifiedCase.Status.QA_IN_PROGRESS,
        report_review_status=Boolean.YES,
    )
    form: MockForm = MockForm(
        cleaned_data={"status": SimplifiedCase.Status.READY_TO_QA}
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.parametrize(
    "search_field",
    ["auditor_id", "reviewer_id"],
)
@pytest.mark.django_db
def test_simplified_case_filtered_by_not_having_an_auditor(search_field):
    """Test that case without auditor or reviewer is found"""
    SimplifiedCase.objects.create()
    form: MockForm = MockForm(cleaned_data={search_field: "none"})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1


@pytest.mark.parametrize(
    "recommendation_for_enforcement_filter, expected_number, expected_name",
    [
        ("", 3, ORGANISATION_NAME_NOT_SELECTED),
        ("no-further-action", 1, ORGANISATION_NAME_NO_FURTHER_ACTION),
        ("other", 1, ORGANISATION_NAME_FOR_ENFORCEMENT),
        ("unknown", 1, ORGANISATION_NAME_NOT_SELECTED),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_recommendation_for_enforcement(
    recommendation_for_enforcement_filter, expected_number, expected_name
):
    """
    Test that filtering by recommendation for enforcement is reflected in the queryset
    """
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_NO_FURTHER_ACTION,
        recommendation_for_enforcement="no-further-action",
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_FOR_ENFORCEMENT,
        recommendation_for_enforcement="other",
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_NOT_SELECTED,
        recommendation_for_enforcement="unknown",
    )
    form: MockForm = MockForm(
        cleaned_data={
            "recommendation_for_enforcement": recommendation_for_enforcement_filter
        }
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.parametrize(
    "is_complaint_filter, expected_number, expected_name",
    [
        ("", 2, ORGANISATION_NAME_COMPLAINT),
        ("no", 1, ORGANISATION_NAME),
        ("yes", 1, ORGANISATION_NAME_COMPLAINT),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_is_complaint(
    is_complaint_filter, expected_number, expected_name
):
    """Test that filtering by complaint is reflected in the queryset"""
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME)
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_COMPLAINT, is_complaint="yes"
    )
    form: MockForm = MockForm(cleaned_data={"is_complaint": is_complaint_filter})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.parametrize(
    "enforcement_body_filter, expected_number, expected_name",
    [
        ("", 2, ORGANISATION_NAME_EHRC),
        ("ehrc", 1, ORGANISATION_NAME_EHRC),
        ("ecni", 1, ORGANISATION_NAME_ECNI),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_enforcement_body(
    enforcement_body_filter, expected_number, expected_name
):
    """Test that filtering by enforcement body is reflected in the queryset"""
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    form: MockForm = MockForm(
        cleaned_data={"enforcement_body": enforcement_body_filter}
    )

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))  # type: ignore

    assert len(filtered_cases) == expected_number
    assert filtered_cases[0].organisation_name == expected_name


@pytest.mark.django_db
def test_case_filtered_by_sector():
    """Test that filtering by sector is reflected in the queryset"""
    sector: Sector = Sector.objects.create()
    SimplifiedCase.objects.create(organisation_name=ORGANISATION_NAME, sector=sector)
    form: MockForm = MockForm(cleaned_data={"sector": sector})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_case_filtered_by_subcategory():
    """Test that filtering by subcategory is reflected in the queryset"""
    subcategory: SubCategory = SubCategory.objects.create()
    SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME, subcategory=subcategory
    )
    form: MockForm = MockForm(cleaned_data={"subcategory": subcategory})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == ORGANISATION_NAME


@pytest.mark.django_db
def test_case_filtered_by_all_test_types():
    """Test filtering cases by all testing types"""
    SimplifiedCase.objects.create(
        organisation_name="Simplified Org", test_type=SimplifiedCase.TestType.SIMPLIFIED
    )
    SimplifiedCase.objects.create(
        organisation_name="Detailed Org", test_type=SimplifiedCase.TestType.DETAILED
    )
    SimplifiedCase.objects.create(
        organisation_name="Mobile Org", test_type=SimplifiedCase.TestType.MOBILE
    )
    form: MockForm = MockForm(cleaned_data={"test_type": ""})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 3
    assert filtered_cases[0].organisation_name == "Mobile Org"
    assert filtered_cases[1].organisation_name == "Detailed Org"
    assert filtered_cases[2].organisation_name == "Simplified Org"


@pytest.mark.parametrize(
    "test_type, expected_organisation",
    [
        (SimplifiedCase.TestType.SIMPLIFIED, "Simplified Org"),
        (SimplifiedCase.TestType.DETAILED, "Detailed Org"),
        (SimplifiedCase.TestType.MOBILE, "Mobile Org"),
    ],
)
@pytest.mark.django_db
def test_case_filtered_by_test_type(test_type, expected_organisation):
    """
    Test that filtering cases by specific testing type is reflected in the queryset
    """
    SimplifiedCase.objects.create(
        organisation_name="Simplified Org", test_type=SimplifiedCase.TestType.SIMPLIFIED
    )
    SimplifiedCase.objects.create(
        organisation_name="Detailed Org", test_type=SimplifiedCase.TestType.DETAILED
    )
    SimplifiedCase.objects.create(
        organisation_name="Mobile Org", test_type=SimplifiedCase.TestType.MOBILE
    )
    form: MockForm = MockForm(cleaned_data={"test_type": test_type})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 1
    assert filtered_cases[0].organisation_name == expected_organisation


@pytest.mark.django_db
def test_cases_ordered_to_put_unassigned_first():
    """Test that case filtering returns unassigned cases first by default"""
    first_created: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_ECNI, enforcement_body="ecni"
    )
    CaseStatus.objects.create(simplified_case=first_created)
    second_created: SimplifiedCase = SimplifiedCase.objects.create(
        organisation_name=ORGANISATION_NAME_EHRC, enforcement_body="ehrc"
    )
    CaseStatus.objects.create(simplified_case=second_created)
    form: MockForm = MockForm(cleaned_data={})

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == second_created.organisation_name

    auditor: User = User.objects.create(
        username="new", first_name="New", last_name="User"
    )
    second_created.auditor = auditor
    second_created.save()
    second_created.update_case_status()

    filtered_cases: list[SimplifiedCase] = list(filter_cases(form))

    assert len(filtered_cases) == 2
    assert filtered_cases[0].organisation_name == first_created.organisation_name


@pytest.mark.django_db
def test_cases_sorted_by_newest_first():
    """Test cases sorted by newest first"""
    base_case_1: BaseCase = BaseCase.objects.create()
    base_case_2: BaseCase = BaseCase.objects.create()
    base_case_3: BaseCase = BaseCase.objects.create()
    form: MockForm = MockForm(cleaned_data={"sort_by": Sort.NEWEST})

    filtered_cases: list[BaseCase] = list(filter_cases(form))

    assert len(filtered_cases) == 3
    assert filtered_cases == [base_case_3, base_case_2, base_case_1]


@pytest.mark.django_db
def test_cases_sorted_by_oldest_first():
    """Test cases sorted by oldest first"""
    base_case_1: BaseCase = BaseCase.objects.create()
    base_case_2: BaseCase = BaseCase.objects.create()
    base_case_3: BaseCase = BaseCase.objects.create()
    form: MockForm = MockForm(cleaned_data={"sort_by": Sort.OLDEST})

    filtered_cases: list[BaseCase] = list(filter_cases(form))

    assert len(filtered_cases) == 3
    assert filtered_cases == [base_case_1, base_case_2, base_case_3]


@pytest.mark.django_db
def test_cases_sorted_by_name():
    """Test cases sorted by name"""
    base_case_1: BaseCase = BaseCase.objects.create(organisation_name="C")
    base_case_2: BaseCase = BaseCase.objects.create(organisation_name="A")
    base_case_3: BaseCase = BaseCase.objects.create(organisation_name="B")
    form: MockForm = MockForm(cleaned_data={"sort_by": Sort.NAME})

    filtered_cases: list[BaseCase] = list(filter_cases(form))

    assert len(filtered_cases) == 3
    assert filtered_cases == [base_case_2, base_case_3, base_case_1]


@pytest.mark.parametrize(
    "url, domain, expected_number_of_duplicates",
    [
        (HOME_PAGE_URL, ORGANISATION_NAME, 2),
        (HOME_PAGE_URL, "", 1),
        ("https://domain2.com", "Org name", 0),
        ("https://domain2.com", "", 0),
    ],
)
@pytest.mark.django_db
def test_find_duplicate_cases(url, domain, expected_number_of_duplicates) -> BaseCase:
    """Test find_duplicate_cases returns matching cases"""
    organisation_name_case: BaseCase = BaseCase.objects.create(
        organisation_name=ORGANISATION_NAME
    )
    domain_case: SimplifiedCase = SimplifiedCase.objects.create(
        home_page_url=HOME_PAGE_URL
    )

    duplicate_cases: list[BaseCase] = list(find_duplicate_cases(url, domain))

    assert len(duplicate_cases) == expected_number_of_duplicates

    if expected_number_of_duplicates > 0:
        assert duplicate_cases[0].case_identifier == domain_case.case_identifier

    if expected_number_of_duplicates > 1:
        assert (
            duplicate_cases[1].case_identifier == organisation_name_case.case_identifier
        )
