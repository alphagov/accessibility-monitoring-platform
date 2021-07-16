"""
Test for loat_test_cases_csv command
"""
import pytest
from datetime import date, datetime
from functools import partial
import pytz
from typing import Callable, Dict, List, Union

from django.contrib.auth.models import User
from django.core.management import call_command

from ...common.models import Region, Sector
from ..management.commands.load_test_cases_csv import (
    delete_existing_data,
    get_users,
    get_regions,
    get_sectors,
    get_boolean_from_row,
    get_string_from_row,
    get_integer_from_row,
    get_date_from_row,
    get_datetime_from_row,
    get_or_create_user_from_row,
    get_or_create_sector_from_row,
    get_data_from_row,
    create_case,
    get_or_create_regions_from_row,
)
from ..models import Case, Contact

USER_NAME: str = "user.name@example.com"
REGION_NAME: str = "Region Name"
SECOND_REGION_NAME: str = "Second Region"
SECTOR_NAME: str = "Sector Name"


@pytest.mark.django_db
def test_delete_existing_data():
    """Test delete_existing_data deletes existing Case and Contact data"""
    case: Case = Case.objects.create()
    Contact.objects.create(case=case)

    assert Case.objects.count() == 1
    assert Contact.objects.count() == 1

    delete_existing_data()

    assert Case.objects.count() == 0
    assert Contact.objects.count() == 0


@pytest.mark.parametrize(
    "get_function, model, field_name, value",
    [
        (get_users, User, "username", "username"),
        (get_regions, Region, "name", "Region Name"),
        (get_sectors, Sector, "name", "Sector Name"),
    ],
)
@pytest.mark.django_db
def test_get_users(get_function, model, field_name, value):
    """Test function returns a dictionary of objects keyed by values"""
    obj: Union[User, Region, Sector] = model.objects.create(**{field_name: value})

    objs: List[Union[User, Region, Sector]] = get_function()

    assert objs == {value: obj}


@pytest.mark.parametrize(
    "row, expected_value",
    [
        ({"column": None}, None),
        ({"column": ""}, None),
        ({"column": "False"}, False),
        ({"column": "True"}, True),
        ({}, None),
    ],
)
def test_get_boolean_from_row(row, expected_value):
    """Test get_boolean_from_row returns correct boolean values"""
    assert get_boolean_from_row(row=row, column_name="column") == expected_value


@pytest.mark.parametrize(
    "row, expected_value",
    [
        ({"column": "xxx"}, "xxx"),
        ({}, ""),
    ],
)
def test_get_string_from_row(row, expected_value):
    """Test get_string_from_row returns string value or empty string"""
    assert get_string_from_row(row=row, column_name="column") == expected_value


def test_get_integer_from_row():
    """Test get_integer_from_row returns an integer"""
    assert get_integer_from_row({"column": "16"}, column_name="column") == 16


@pytest.mark.parametrize(
    "row, expected_value",
    [
        ({"column": "2020-01-01"}, date(2020, 1, 1)),
        ({"column": ""}, None),
        ({}, None),
    ],
)
def test_get_date_from_row(row, expected_value):
    """Test get_date_from_row returns date or none"""
    assert get_date_from_row(row=row, column_name="column") == expected_value


@pytest.mark.parametrize(
    "row, expected_value",
    [
        (
            {"column": "2021-06-28 11:13:28.107107+00:00"},
            datetime(2021, 6, 28, 11, 13, 28, 107107, tzinfo=pytz.UTC),
        ),
        (
            {"column": "2020-02-19 00:00:00+00:00"},
            datetime(2020, 2, 19, 0, 0, 0, tzinfo=pytz.UTC),
        ),
        ({"column": ""}, None),
        ({}, None),
    ],
)
def test_get_datetime_from_row(row, expected_value):
    """Test get_date_from_row returns timestamp or none"""
    assert get_datetime_from_row(row=row, column_name="column") == expected_value


@pytest.mark.parametrize("row", [{"column": ""}, {}])
def test_get_or_create_user_from_row_returns_none_if_no_user_in_row(row):
    """Test get_or_create_user_from_row returns none if no user in row"""
    users: Dict = {}

    assert (
        get_or_create_user_from_row(row=row, users=users, column_name="column") is None
    )


@pytest.mark.django_db
def test_get_or_create_user_from_row_returns_user():
    """Test get_or_create_user_from_row returns user matching username"""
    user: User = User.objects.create(username=USER_NAME)
    users: dict[str, User] = {USER_NAME: user}
    row: Dict[str, str] = {"column": USER_NAME}

    assert (
        get_or_create_user_from_row(row=row, users=users, column_name="column") == user
    )


@pytest.mark.django_db
def test_get_or_create_user_from_row_creates_user():
    """Test get_or_create_user_from_row creates user if no matching user found"""
    users: Dict = {}
    row: Dict[str, str] = {"column": USER_NAME}

    assert User.objects.count() == 0

    user: User = get_or_create_user_from_row(row=row, users=users, column_name="column")

    assert user.username == USER_NAME
    assert User.objects.count() == 1


@pytest.mark.parametrize("row", [{"sector": ""}, {}])
def test_get_or_create_sector_from_row_returns_none_if_no_sector_in_row(row):
    """Test get_or_create_sector_from_row returns none if no sector in row"""
    sectors: Dict = {}

    assert get_or_create_sector_from_row(row=row, sectors=sectors) is None


@pytest.mark.django_db
def test_get_or_create_sector_from_row_returns_sector():
    """Test get_or_create_sector_from_row returns sector matching name"""
    sector: Sector = Sector.objects.create(name=SECTOR_NAME)
    sectors: Dict[str, Sector] = {SECTOR_NAME: sector}
    row: Dict[str, str] = {"sector": SECTOR_NAME}

    assert get_or_create_sector_from_row(row=row, sectors=sectors) == sector


@pytest.mark.django_db
def test_get_or_create_sector_from_row_creates_sector():
    """Test get_or_create_sector_from_row creates sector if no matching sector found"""
    sectors: Dict = {}
    row: Dict[str, str] = {"sector": SECTOR_NAME}

    assert Sector.objects.count() == 0

    sector: Sector = get_or_create_sector_from_row(row=row, sectors=sectors)

    assert sector.name == SECTOR_NAME
    assert Sector.objects.count() == 1


@pytest.mark.parametrize(
    "column_name, column_type, expected_value",
    [
        ("name", "string", "squiggle"),
        ("flag", "boolean", True),
        ("id", "integer", 4),
        ("sent", "date", date(2021, 2, 28)),
        ("created", "datetime", datetime(2020, 2, 19, 0, 0, 0, tzinfo=pytz.UTC)),
        ("auditor", "user", "user1"),
        ("sector", "sector", "sector1"),
    ],
)
def test_get_data_from_row(column_name, column_type, expected_value):
    """Test get_date_from_row returns timestamp or none"""
    row: Dict[str, str] = {
        "name": "squiggle",
        "flag": "True",
        "id": "4",
        "sent": "2021-02-28",
        "created": "2020-02-19 00:00:00+00:00",
        "auditor": USER_NAME,
        "sector": SECTOR_NAME,
    }
    users: Dict[str, str] = {USER_NAME: "user1"}
    sectors: dict[str, str] = {SECTOR_NAME: "sector1"}

    assert (
        get_data_from_row(
            row=row,
            users=users,
            sectors=sectors,
            column_name=column_name,
            column_type=column_type,
        )
        == expected_value
    )


@pytest.mark.django_db
def test_create_case_creates_a_case():
    """Test create_case creates a case"""
    case_id: str = "7"
    row: Dict[str, str] = {
        "id": case_id,
        "is_public_sector_body": "True",
        "is_website_compliant": "False",
        "is_website_retested": "False",
        "is_disproportionate_claimed": "False",
        "is_case_completed": "False",
        "is_archived": "False",
    }

    get_data: Callable = partial(get_data_from_row, row=row, users={}, sectors={})

    assert Case.objects.count() == 0

    case: Case = create_case(get_data)

    assert Case.objects.count() == 1
    assert case.id == int(case_id)


@pytest.mark.parametrize("row", [{"regions": ""}, {}])
def test_get_or_create_regions_from_row_returns_none_if_no_sector_in_row(row):
    """Test get_or_create_regions_from_row returns none if no regions in row"""
    regions: Dict = {}

    assert get_or_create_regions_from_row(row=row, regions=regions) == []


@pytest.mark.django_db
def test_get_or_create_regions_from_row_returns_sector():
    """Test get_or_create_regions_from_row returns regions matching names"""
    first_region: Region = Region.objects.create(name=REGION_NAME)
    second_region: Region = Region.objects.create(name=SECOND_REGION_NAME)
    regions: Dict[str, Region] = {
        REGION_NAME: first_region,
        SECOND_REGION_NAME: second_region,
    }
    row: Dict[str, str] = {"region": f"{REGION_NAME},{SECOND_REGION_NAME}"}

    assert get_or_create_regions_from_row(row=row, regions=regions) == [
        first_region,
        second_region,
    ]


@pytest.mark.django_db
def test_get_or_create_regions_from_row_creates_regions():
    """Test get_or_create_regions_from_row creates regions if no matching region found"""
    regions: Dict = {}
    row: Dict[str, str] = {"region": f"{REGION_NAME},{SECOND_REGION_NAME}"}

    assert Region.objects.count() == 0

    regions: List[Region] = get_or_create_regions_from_row(row=row, regions=regions)

    assert Region.objects.count() == 2
    assert regions[0].name == REGION_NAME
    assert regions[1].name == SECOND_REGION_NAME


@pytest.mark.django_db
def test_load_test_cases_csv_command():
    """Test load_test_cases_csv populates the database"""
    call_command("load_test_cases_csv", "--initial")

    assert Case.objects.count() == 21
    assert Contact.objects.count() == 7
