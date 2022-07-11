"""test_parse_json.py - contains tests for parse_json.py"""
import io
import json
import os
from typing import List, TypedDict
from unittest import mock

import pytest
from deploy_feature_to_paas.app.parse_json import (
    validate_json_dict,
    parse_settings_json,
)


def test_validate_json_dict_validates_successfully():
    """Tests if dictionary validates correctly with TypedDict"""
    data = {"string": "string", "num": 1, "list": [1, 2, 3]}

    class DataType(TypedDict):
        string: str
        num: int
        list: List[str]

    assert validate_json_dict(data, DataType)


def test_validate_json_dict__detects_extra_data():
    """Tests if validate_json_dict identifies additional data fields"""
    data = {"string": "string", "num": 1, "list": [1, 2, 3], "extra_fields": 1}

    class DataType(TypedDict):
        string: str
        num: int
        list: List[str]

    with pytest.raises(Exception) as exc_info:
        validate_json_dict(data, DataType)

    assert "Missing or invalid values in json settings file" in exc_info.value.args[0]
    assert "extra_fields" in exc_info.value.args[0]


def test_validate_json_dict_detects_missing_data():
    """Tests if validate_json_dict identifies missing data fields"""
    data = {
        "string": "string",
        "num": 1,
    }

    class DataType(TypedDict):
        string: str
        num: int
        list: List[str]

    with pytest.raises(Exception) as exc_info:
        validate_json_dict(data, DataType)

    assert "Missing or invalid values in json settings file" in exc_info.value.args[0]
    assert "list" in exc_info.value.args[0]


def test_validate_json_dict_detects_incorrect_types():
    """Tests if validate_json_dict detects incorrect data types"""
    data = {
        "string": "string",
        "num": 1,
        "list_int": [1, 2, 3],
    }

    class DataType(TypedDict):
        string: int
        num: int
        list_int: List[int]

    with pytest.raises(Exception) as exc_info:
        validate_json_dict(data, DataType)

    assert "Types in json were invalid" in exc_info.value.args[0]
    assert (
        "string should be <class 'int'> is currently <class 'str'>"
        in exc_info.value.args[0]
    )


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_parse_settings_json(mock_stdout):
    """Tests if parse_settings_json returns a dictionary object"""
    json_data = "data.json"
    data = {
        "name": "str",
        "date": "str",
        "space_name": "str",
        "app_name": "str",
        "db_name": "str",
        "db_ping_attempts": 1,
        "db_ping_interval": 1,
        "template_path": "str",
        "temp_manifest_path": "str",
        "db_space_to_copy": "str",
        "db_instance_to_copy": "str",
        "temp_db_copy_path": "str",
        "s3_bucket": "str",
        "backup_db": True,
        "s3_report_store": "str",
        "report_viewer_app_name": "str",
    }

    with open(json_data, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    res = parse_settings_json(json_data)
    os.remove(json_data)

    assert res == data

    assert ">>> Settings loaded correctly" in mock_stdout.getvalue()
    assert ">>> loaded from data.json" in mock_stdout.getvalue()
    assert ">>> using str" in mock_stdout.getvalue()
    assert ">>> date str" in mock_stdout.getvalue()
