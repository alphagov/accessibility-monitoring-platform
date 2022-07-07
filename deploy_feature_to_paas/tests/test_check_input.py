import io
from unittest import mock

from deploy_feature_to_paas.app.parse_json import SettingsType
from deploy_feature_to_paas.app.check_input import print_prototype_settings


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_check_input_outputs_the_correct_information(mock_stdout):
    """Test whether check_input prints the correct settings"""
    data: SettingsType = {
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

    res = print_prototype_settings(data)
    assert res
    assert "This script will create a new environment:" in mock_stdout.getvalue()
    assert "Copying database from:" in mock_stdout.getvalue()
    assert data["db_space_to_copy"] in mock_stdout.getvalue()
    assert data["db_instance_to_copy"] in mock_stdout.getvalue()
    assert data["space_name"] in mock_stdout.getvalue()
    assert data["app_name"] in mock_stdout.getvalue()
    assert data["report_viewer_app_name"] in mock_stdout.getvalue()
    assert data["db_name"] in mock_stdout.getvalue()
    assert data["s3_report_store"] in mock_stdout.getvalue()
    assert "The database will back up to S3" in mock_stdout.getvalue()
