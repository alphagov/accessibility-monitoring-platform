"""test_main.py - contains tests for main.py"""
import io
from unittest import mock

from deploy_feature_to_paas.main import main


config_1 = {
    "name": "deploy_feature_settings_0.2.1",
    "date": "20220309",
    "space_name": "git_branch",
    "app_name": "git_branch",
    "report_viewer_app_name": "git_branch",
    "db_name": "db",
    "db_ping_attempts": 1,
    "db_ping_interval": 1,
    "template_path": "./manifest_template.txt",
    "temp_manifest_path": "./temp_manifest.yml",
    "db_space_to_copy": "monitoring-platform",
    "db_instance_to_copy": "monitoring-platform-default-db",
    "temp_db_copy_path": "./backup.sql",
    "s3_bucket": "s3_bucket",
    "s3_report_store": "s3_bucket",
    "backup_db": False,
}

config_2 = {
    "name": "deploy_feature_settings_0.2.1",
    "date": "20220309",
    "space_name": "100_git_branch",
    "app_name": "100_git_branch",
    "report_viewer_app_name": "100_git_branch",
    "db_name": "db",
    "db_ping_attempts": 1,
    "db_ping_interval": 1,
    "template_path": "./manifest_template.txt",
    "temp_manifest_path": "./temp_manifest.yml",
    "db_space_to_copy": "monitoring-platform",
    "db_instance_to_copy": "db",
    "temp_db_copy_path": "./backup.sql",
    "s3_bucket": "s3_bucket",
    "s3_report_store": "s3_bucket",
    "backup_db": False,
}


@mock.patch("deploy_feature_to_paas.main.BuildEnv")
@mock.patch("deploy_feature_to_paas.main.upload_db_to_s3")
@mock.patch("deploy_feature_to_paas.main.CopyDB")
@mock.patch("deploy_feature_to_paas.main.check_input")
@mock.patch("deploy_feature_to_paas.main.check_if_cf_logged_in")
@mock.patch("deploy_feature_to_paas.main.reconfigure_config_file")
@mock.patch("deploy_feature_to_paas.main.parse_settings_json")
@mock.patch("argparse.ArgumentParser.parse_args")
@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_main_completes_successfully(
    mock_stdout,
    mock_parser,
    mock_parse_settings_json,
    mock_reconfigure_config_file,
    mock_check_if_cf_logged_in,
    mock_check_input,
    mock_copydb,
    mock_upload_db_to_s3,
    mock_build_env,
):
    """Tests if main function completes successfully"""

    class MockParser:
        build_direction = "up"
        settings_json = "./file.json"
        force = False

    mock_parser.return_value = MockParser
    mock_parse_settings_json.return_value = config_1
    mock_reconfigure_config_file.return_value = config_2
    mock_check_if_cf_logged_in.return_value = True
    mock_check_input.return_value = True
    mock_copydb.return_value.start.return_value = True
    mock_copydb.return_value.clean_up.return_value = True
    mock_copydb.return_value.change_space.return_value = True
    mock_upload_db_to_s3.return_value = True
    mock_build_env.return_value.start.return_value = True
    mock_build_env.return_value.clean_up.return_value = True
    assert main()
    assert (
        "deploys_feature_to_paas creates a new environment in PaaS for testing new features"
        in mock_stdout.getvalue()
    )
    assert "Process took" in mock_stdout.getvalue()
