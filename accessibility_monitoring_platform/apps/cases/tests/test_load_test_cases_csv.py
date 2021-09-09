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
from django.db import models

from ...common.models import Sector
from ..management.commands.load_test_cases_csv import (
    delete_existing_data,
    get_users,
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
)
from ..models import Case, Contact

USER_NAME: str = "user.name@example.com"
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
        (get_sectors, Sector, "name", "Sector Name"),
    ],
)
@pytest.mark.django_db
def test_get_users(get_function, model, field_name, value):
    """Test function returns a dictionary of objects keyed by values"""
    obj: Union[User, Sector] = model.objects.create(**{field_name: value})

    objs: List[Union[User, Sector]] = get_function()

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
    "field, expected_value",
    [
        (models.CharField(name="name"), "squiggle"),
        (models.BooleanField(name="flag"), True),
        (models.IntegerField(name="id"), 4),
        (models.DateField(name="sent"), date(2021, 2, 28)),
        (
            models.DateTimeField(name="created"),
            datetime(2020, 2, 19, 0, 0, 0, tzinfo=pytz.UTC),
        ),
        (
            models.ForeignKey(name="auditor", to=User, on_delete=models.DO_NOTHING),
            "user1",
        ),
        (
            models.ForeignKey(name="sector", to=Sector, on_delete=models.DO_NOTHING),
            "sector1",
        ),
    ],
)
def test_get_data_from_row(field, expected_value):
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
            field=field,
        )
        == expected_value
    )


@pytest.mark.django_db
def test_create_case_creates_a_case():
    """Test create_case creates a case"""
    case_id: str = "7"
    row: Dict[str, str] = {
        "id": case_id,
        "is_website_compliant": "False",
        "is_website_retested": "False",
        "is_disproportionate_claimed": "False",
        "is_deleted": "False",
        "no_psb_contact": "False",
        "report_is_approved": "False",
        "report_is_ready_to_review": "False",
    }

    get_data: Callable = partial(get_data_from_row, row=row, users={}, sectors={})

    assert Case.objects.count() == 0

    case: Case = create_case(get_data)

    assert Case.objects.count() == 1
    assert case.id == int(case_id)


@pytest.mark.django_db
def test_load_test_cases_csv_command():
    """Test load_test_cases_csv populates the database"""
    call_command("load_test_cases_csv", "--initial")

    assert Case.objects.count() == 21
    assert Contact.objects.count() == 6
