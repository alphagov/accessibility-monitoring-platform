from deploy_feature_to_paas.main import (
    check_if_cf_logged_in,
    reconfigure_config_file,
)
from deploy_feature_to_paas.app.parse_json import SettingsType
import pytest
from unittest import mock


@mock.patch("subprocess.Popen")
def test_check_if_cf_logged_in_return_true(mock_popen):
    successful_res_from_cf = b"""
Getting spaces in org ORGANISATION as firstname.lastname@cabinet-office.gov.uk...

name
space_name1
space_name2
"""
    mock_popen.return_value.communicate.return_value = (successful_res_from_cf, b"")
    assert check_if_cf_logged_in()


@mock.patch("subprocess.Popen")
def test_check_if_cf_logged_in_raise_exception(mock_popen):
    failed_res_from_cf = b"""
Getting spaces in org ORGANISATION as firstname.lastname@cabinet-office.gov.uk...

The token expired, was revoked, or the token ID is incorrect. Please log back in to re-authenticate.
FAILED    
"""
    mock_popen.return_value.communicate.return_value = (failed_res_from_cf, b"")

    with pytest.raises(Exception) as e:
        check_if_cf_logged_in()

    assert "Error not logged into CF" in str(e)


@mock.patch("os.environ.get")
@mock.patch("subprocess.check_output")
def test_reconfigure_config_file_calculates_new_values(mock_check_output, mock_os):
    mock_check_output.return_value = b"""100-current-git-branch"""
    mock_os.return_value = "users_name"

    config: SettingsType = {
        "name": "deploy_feature_settings_0.2.1",
        "date": "20220309",
        "space_name": "git_branch",
        "app_name": "git_branch",
        "report_viewer_app_name": "git_branch",
        "db_name": "monitoring-platform-default-db",
        "db_ping_attempts": 21,
        "db_ping_interval": 30,
        "template_path": "./deploy_feature_to_paas/manifest_template.txt",
        "temp_manifest_path": "./temp_manifest.yml",
        "db_space_to_copy": "monitoring-platform-test",
        "db_instance_to_copy": "monitoring-platform-default-db",
        "temp_db_copy_path": "./backup.sql",
        "s3_bucket": "paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914",
        "s3_report_store": "s3-report-store-prototype",
        "backup_db": False,
    }

    res: SettingsType = reconfigure_config_file(config)
    assert res["space_name"] == "user--100-current-git-branch"
    assert res["app_name"] == "100-current-git-branch"
    assert res["report_viewer_app_name"] == "100-current-git-branch-report-viewer"


@mock.patch("os.environ.get")
@mock.patch("subprocess.check_output")
def test_reconfigure_config_file_uses_original_values(mock_check_output, mock_os):
    mock_check_output.return_value = b"""100-current-git-branch"""
    mock_os.return_value = "users_name"

    config: SettingsType = {
        "name": "deploy_feature_settings_0.2.1",
        "date": "20220309",
        "space_name": "custom_space_name",
        "app_name": "custom_app_name",
        "report_viewer_app_name": "custom_report_viewer_app_name",
        "db_name": "monitoring-platform-default-db",
        "db_ping_attempts": 21,
        "db_ping_interval": 30,
        "template_path": "./deploy_feature_to_paas/manifest_template.txt",
        "temp_manifest_path": "./temp_manifest.yml",
        "db_space_to_copy": "monitoring-platform-test",
        "db_instance_to_copy": "monitoring-platform-default-db",
        "temp_db_copy_path": "./backup.sql",
        "s3_bucket": "paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914",
        "s3_report_store": "s3-report-store-prototype",
        "backup_db": False,
    }

    res: SettingsType = reconfigure_config_file(config)
    assert res["space_name"] == "custom_space_name"
    assert res["app_name"] == "custom_app_name"
    assert res["report_viewer_app_name"] == "custom_report_viewer_app_name"
