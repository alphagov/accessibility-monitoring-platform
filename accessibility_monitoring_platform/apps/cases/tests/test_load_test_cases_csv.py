import pytest
from datetime import date, datetime
import pytz

from django.contrib.auth.models import User

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
)
from ..models import Case, Contact

USER_NAME = "user.name@example.com"
REGION_NAME = "Region Name"
SECTOR_NAME = "Sector Name"


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
    obj = model.objects.create(**{field_name: value})

    objs = get_function()

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
    users = {}

    assert get_or_create_user_from_row(row=row, users=users, column_name="column") is None


@pytest.mark.django_db
def test_get_or_create_user_from_row_returns_user():
    """Test get_or_create_user_from_row returns user matching username"""
    user = User.objects.create(username=USER_NAME)
    users = {USER_NAME: user}
    row = {"column": USER_NAME}

    assert get_or_create_user_from_row(row=row, users=users, column_name="column") == user


@pytest.mark.django_db
def test_get_or_create_user_from_row_creates_user():
    """Test get_or_create_user_from_row creates user if no matching user found"""
    users = {}
    row = {"column": USER_NAME}

    assert User.objects.count() == 0

    user = get_or_create_user_from_row(row=row, users=users, column_name="column")

    assert user.username == USER_NAME
    assert User.objects.count() == 1
