""" parse_json - parses settings json"""
import os
from pathlib import Path
from typing import Any, TypedDict, Union, List
import json


class SettingsType(TypedDict):
    """Dictionary type for settings

    Args:
        TypedDict ([type]): Type for integration test object
    """
    name: str
    date: str
    space_name: str
    app_name: str
    db_name: str
    db_ping_attempts: int
    db_ping_interval: int
    template_path: str
    temp_manifest_path: str
    db_space_to_copy: str
    db_instance_to_copy: str
    temp_db_copy_path: str
    s3_bucket: str
    backup_db: bool


def validate_json_dict(data: Any, class_type: Any) -> None:
    """Very basic type checker for dictionary. Does not check embedded dictionaries.
    If checking fails, it raises an error

    Args:
        data (dictionary): dictionary to type check
        class_type (class): class to check dictionary against
    """
    class_keys: List[str] = list(class_type.__dict__["__annotations__"])
    data_keys: List[str] = list(data)
    diff: List[str] = list(set(class_keys) - set(data_keys))
    diff2: List[str] = list(set(data_keys) - set(class_keys))

    invalid_fields = []
    if diff or diff2:  # Detects if there are missing fields in JSON
        missing: str = ""
        extra: str = ""
        if diff:
            missing = f"""\n    Missing from integration settings - {", ".join(diff)}"""
        if diff2:
            extra = f"""\n    Extra fields in json - {", ".join(diff2)}"""
        raise Exception(f"Missing or invalid values in json settings file - {missing} {extra}")

    for key in data:
        if key in data:
            if (
                type(data[key]) != class_type.__dict__["__annotations__"][key]
                and (
                    type(data[key]) != list
                    or "typing.List[" not in str(class_type.__dict__["__annotations__"][key])
                )
            ):
                invalid_fields.append(key)

    if invalid_fields:  # Detects if the types in JSON are incorrect
        type_guide: str = ""
        for field in invalid_fields:
            type_guide += f"""\n    - {field} should be {class_type.__dict__["__annotations__"][field]} is currently {type(data[field])}"""
        raise Exception(f"""Types in integration settings json were invalid: {type_guide}""")


def parse_settings_json(settings_path: Union[str, None] = None) -> SettingsType:
    """Loads integrations settings json. Defaults to ./stack_tests/integration_tests_settings.json if
    no file name is given.

    Args:
        settings_path (Union[str, None], optional): Path for integrations settings file. Defaults to None.

    Returns:
        SettingsType: Settings data as dictionary
    """
    if settings_path is None:
        dir_path: str = os.path.dirname(os.path.realpath(__file__))
        path: Path = Path(dir_path)
        settings_path = f"{path.parent.absolute()}/deploy_feature_settings.json"

    with open(file=settings_path) as fp:
        contents: str = fp.read()
    settings: SettingsType = json.loads(contents)
    validate_json_dict(settings, SettingsType)
    print(">>> Settings loaded correctly")
    print(f">>> loaded from {settings_path}")
    print(f""">>> using {settings["name"]}""")
    print(f""">>> date {settings["date"]}""")
    return settings
