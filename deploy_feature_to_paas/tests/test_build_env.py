"""test_build_env - contains tests for build_env.py"""
import io
import os
from unittest import mock
from typing import Any, TypedDict

import boto3
from moto import mock_s3
import pytest

from deploy_feature_to_paas.app.parse_json import SettingsType
from deploy_feature_to_paas.app.build_env import BuildEnv


PAAS_SETTINGS: SettingsType = {
    "name": "name",
    "date": "010120202",
    "space_name": "space_name",
    "app_name": "app_name",
    "db_name": "db_name",
    "db_ping_attempts": 1,
    "db_ping_interval": 0,
    "template_path": "./template_path.txt",
    "temp_manifest_path": "./temp_manifest.yml",
    "db_space_to_copy": "db_space",
    "db_instance_to_copy": "db_instance",
    "temp_db_copy_path": "temp_db",
    "s3_bucket": "s3_bucket",
    "backup_db": True,
    "s3_report_store": "str",
    "report_viewer_app_name": "str",
}

REPORT_VIEWER_APP_NAME: str = "report_viewer_app_name"


class ValidBuildEnvDataType(TypedDict):
    """Data type for build env settings"""

    build_direction: str
    space_name: str
    app_name: str
    report_viewer_app_name: str
    db_name: str
    template_object: Any
    template_path: str
    manifest_path: str
    temp_db_copy_path: str
    s3_report_store: str
    db_ping_attempts: int
    db_ping_interval: int


DEFAULT_BUILD_ENV_SETTINGS: ValidBuildEnvDataType = {
    "build_direction": "up",
    "space_name": PAAS_SETTINGS["space_name"],
    "app_name": PAAS_SETTINGS["app_name"],
    "report_viewer_app_name": REPORT_VIEWER_APP_NAME,
    "db_name": PAAS_SETTINGS["db_name"],
    "template_object": {},
    "template_path": PAAS_SETTINGS["template_path"],
    "manifest_path": PAAS_SETTINGS["temp_manifest_path"],
    "temp_db_copy_path": PAAS_SETTINGS["temp_db_copy_path"],
    "s3_report_store": PAAS_SETTINGS["s3_report_store"],
    "db_ping_attempts": PAAS_SETTINGS["db_ping_attempts"],
    "db_ping_interval": PAAS_SETTINGS["db_ping_interval"],
}


def test_build_env_incorrect_build_direction_raises_exception():
    """Tests if BuildEnv raises exception if build_correction isn't valid"""
    build_env_settings: ValidBuildEnvDataType = DEFAULT_BUILD_ENV_SETTINGS.copy()
    build_env_settings["build_direction"] = "WRONG VALUE"
    with pytest.raises(Exception) as exc_info:
        BuildEnv(**build_env_settings)

    assert "build_direction needs to be up or down" in exc_info.value.args[0]


@pytest.mark.parametrize(
    "space_name, app_name, exception",
    [
        (
            "monitoring-platform-production",
            "app_name",
            "monitoring-platform-production is a protected space_name",
        ),
        (
            "monitoring-platform-test",
            "app_name",
            "monitoring-platform-test is a protected space_name",
        ),
        (
            "space_name",
            "accessibility-monitoring-platform-production",
            "accessibility-monitoring-platform-production is a protected app_name",
        ),
        (
            "space_name",
            "accessibility-monitoring-platform-test",
            "accessibility-monitoring-platform-test is a protected app_name",
        ),
    ],
)
def test_build_env_init_raises_exception_if_using_protected_space_names(
    space_name, app_name, exception
):
    """Tests if protected space names are used"""
    build_env_settings: ValidBuildEnvDataType = DEFAULT_BUILD_ENV_SETTINGS.copy()
    build_env_settings["space_name"] = space_name
    build_env_settings["app_name"] = app_name
    with pytest.raises(Exception) as exc_info:
        BuildEnv(**build_env_settings)

    assert exception in exc_info.value.args[0]


@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.down")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.up")
def test_build_env_start_works_correctly_up(mock_buildenv_up, mock_buildenv_down):
    """Tests if build direction is correctly routed in start()"""
    build_env: BuildEnv = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    build_env.start()
    assert mock_buildenv_up.called
    assert not mock_buildenv_down.called


@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.down")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.up")
def test_build_env_start_works_correctly_down(mock_buildenv_up, mock_buildenv_down):
    """Tests if build direction is correctly routed in start()"""
    build_env_settings: ValidBuildEnvDataType = DEFAULT_BUILD_ENV_SETTINGS.copy()
    build_env_settings["build_direction"] = "down"
    build_env: BuildEnv = BuildEnv(**build_env_settings)
    build_env.start()
    assert not mock_buildenv_up.called
    assert mock_buildenv_down.called


@mock.patch("sys.stdout", new_callable=io.StringIO)
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.bash_command")
def test_build_env_check_db_has_started_works_correctly(mock_bash_command, mock_stdout):
    """Tests if it correctly detects the database has started"""
    build_env: BuildEnv = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    mock_bash_command.return_value = True
    assert build_env.check_db_has_started()
    assert ">>> pinging database" in mock_stdout.getvalue()
    assert ">>> sleeping for 0 seconds" in mock_stdout.getvalue()
    assert (
        f""">>> {PAAS_SETTINGS["db_name"]} started successfully"""
        in mock_stdout.getvalue()
    )


@mock.patch("subprocess.Popen")
def test_build_env_check_db_has_started_raises_exception(mock_popen):
    """Tests if check_db_has_started() raises exception when it cant connect to the database"""
    build_env: BuildEnv = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    # mock_popen mocks the result from a CF command that checks whether the database has started.
    # It will raise an exception as the mocked command says the database did not start correctly
    mock_popen.return_value.command.return_value = (
        b"Service instance database-name not found",
        b"",
    )
    with pytest.raises(Exception) as exc_info:
        build_env.check_db_has_started()

    assert "Database did not build in time limit" in exc_info.value.args[0]


@mock.patch("sys.stdout", new_callable=io.StringIO)
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.bash_command")
def test_build_env_check_db_has_stopped_works_correctly(mock_bash_command, mock_stdout):
    build_env: BuildEnv = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    mock_bash_command.return_value = True
    assert build_env.check_db_has_stopped()
    assert ">>> pinging database" in mock_stdout.getvalue()
    assert (
        f""">>> {PAAS_SETTINGS["db_name"]} has been removed""" in mock_stdout.getvalue()
    )


@mock.patch("subprocess.Popen")
def test_build_env_check_db_has_stopped_raises_exception(mock_popen):
    """Tests if check_db_has_stopped() raises Exception when database cant be removed"""
    build_env: BuildEnv = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    mock_popen.return_value.command.return_value = (b"", b"")

    with pytest.raises(Exception) as exc_info:
        build_env.check_db_has_stopped()

    assert "Database could not be removed" in exc_info.value.args[0]


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_create_manifest_completes_successfully(mock_stdout):
    """Tests whether create_manifest() correctly produces CF manifest"""
    template_content: str = """
        - $app_name
        - $db
        - $s3_report_store
        - $secret_key
        - $report_viewer_app_name
        - $PORT
    """
    with open(PAAS_SETTINGS["template_path"], "w", encoding="utf-8") as f:
        f.write(template_content)

    template_object = {
        "app_name": PAAS_SETTINGS["app_name"],
        "report_viewer_app_name": PAAS_SETTINGS["report_viewer_app_name"],
        "secret_key": "123456789",
        "db": PAAS_SETTINGS["db_name"],
        "s3_report_store": PAAS_SETTINGS["s3_report_store"],
        "PORT": "8080",
    }

    build_env_settings: ValidBuildEnvDataType = DEFAULT_BUILD_ENV_SETTINGS.copy()
    build_env_settings["template_object"] = template_object
    build_env = BuildEnv(**build_env_settings)

    assert build_env.create_manifest()
    assert ">>> creating manifest" in mock_stdout.getvalue()

    with open(PAAS_SETTINGS["temp_manifest_path"], "r", encoding="utf-8") as f:
        res = f.read()

    assert template_object["app_name"] in res
    assert template_object["report_viewer_app_name"] in res
    assert template_object["secret_key"] in res
    assert template_object["db"] in res
    assert template_object["s3_report_store"] in res
    assert template_object["PORT"] in res

    os.remove(PAAS_SETTINGS["template_path"])
    os.remove(PAAS_SETTINGS["temp_manifest_path"])


def test_clean_up_runs_successfully():
    """Tests if clean_up() correctly cleans up files"""
    with open(PAAS_SETTINGS["temp_manifest_path"], "w", encoding="utf-8") as f:
        f.write("Create a new text file!")

    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    assert build_env.clean_up()
    assert not os.path.exists(PAAS_SETTINGS["temp_manifest_path"])


@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.create_requirements")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.bash_command")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.check_db_has_started")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.install_conduit")
@mock.patch("os.system")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.create_manifest")
@mock.patch("subprocess.run")
@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_up_command_completes_successfully(
    mock_stdout,
    mock_subprocess_run,
    mock_create_manifest,
    mock_os_system,
    mock_install_conduit,
    mock_check_db_has_started,
    mock_bash_command,
    mock_create_requirements,
):
    """Tests if up() completes successfully"""
    mock_create_requirements.return_value = True
    mock_bash_command.return_value = True
    mock_check_db_has_started.return_value = True
    mock_install_conduit.return_value = True
    mock_os_system.return_value = True
    mock_create_manifest.return_value = True
    mock_subprocess_run.return_value = True
    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)

    assert build_env.up()
    assert (
        f""">>> website: {PAAS_SETTINGS["app_name"]}.london.cloudapps.digital"""
        in mock_stdout.getvalue()
    )
    assert (
        f""">>> website: {REPORT_VIEWER_APP_NAME}.london.cloudapps.digital"""
        in mock_stdout.getvalue()
    )


@mock.patch("subprocess.Popen")
@mock.patch("subprocess.check_output")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.bash_command")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.remove_s3_bucket")
@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_down_command_completes_successfully(
    mock_stdout,
    mock_remove_s3_bucket,
    mock_bash_command,
    mock_subprocess_check_output,
    mock_popen,
):
    """Tests down() command completes successfully"""
    mock_remove_s3_bucket.return_value = True
    mock_subprocess_check_output.return_value.decode.return_value = ""
    mock_bash_command.return_value = True
    cf_spaces = """
        name
        cf_space1
        cf_space2
        cf_space3
    """
    mock_popen.return_value.communicate.return_value = (bytes(cf_spaces, "utf-8"), b"")
    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    assert build_env.down()
    assert mock_bash_command.called
    assert (
        f">>> {PAAS_SETTINGS['space_name']} has been deleted" in mock_stdout.getvalue()
    )


@mock.patch("subprocess.Popen")
@mock.patch("subprocess.check_output")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.bash_command")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.remove_s3_bucket")
def test_down_command_raises_exception(
    mock_remove_s3_bucket,
    mock_bash_command,
    mock_subprocess_check_output,
    mock_popen,
):
    """Tests if down command raises exception when CF space doesn't break down"""
    mock_remove_s3_bucket.return_value = True
    mock_subprocess_check_output.return_value.decode.return_value = ""
    mock_bash_command.return_value = True
    cf_spaces = f"""
name
cf_space1
cf_space2
{PAAS_SETTINGS["space_name"]}
"""
    mock_popen.return_value.communicate.return_value = (bytes(cf_spaces, "utf-8"), b"")
    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    with pytest.raises(Exception) as exc_info:
        build_env.down()

    assert (
        f"""{PAAS_SETTINGS["space_name"]} did not break down correctly"""
        in exc_info.value.args[0]
    )

    mock_subprocess_check_output.return_value.decode.return_value = """
        name                                          requested state   processes   routes
        accessibility-monitoring-platform-test        started           web:1/1
    """
    mock_popen.return_value.communicate.return_value = (bytes(cf_spaces, "utf-8"), b"")
    with pytest.raises(Exception) as exc_info:
        build_env.down()

    assert (
        "The prototype build detected it may be in the testing env"
        in exc_info.value.args[0]
    )

    mock_subprocess_check_output.return_value.decode.return_value = """
        name                                          requested state   processes   routes
        accessibility-monitoring-platform-production        started           web:1/1
    """
    mock_popen.return_value.communicate.return_value = (bytes(cf_spaces, "utf-8"), b"")
    with pytest.raises(Exception) as exc_info:
        build_env.down()

    assert (
        "The prototype build detected it may be in the production env"
        in exc_info.value.args[0]
    )


@mock.patch("os.system")
@mock.patch("os.popen")
@mock.patch("deploy_feature_to_paas.app.build_env.BuildEnv.get_aws_credentials")
@mock_s3
def test_remove_s3_bucket_runs_successfully(
    mock_get_aws_credentials,
    mock_os_popen,
    mock_os_system,
):
    """Tests whether S3 bucket completes successfully"""
    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)
    mock_os_system.return_value = True
    mock_os_popen.return_value.read.return_value = """
name             service         plan      bound apps   last operation     broker
db_name          aws-s3-bucket   default                create succeeded   s3-broker
"""
    aws_credentials = {
        "aws_access_key_id": "ACCESS_ID_12345",
        "aws_region": "us-east-1",
        "aws_secret_access_key": "SECRET_KEY_12345",
        "bucket_name": "BUCKET_NAME",
    }
    mock_get_aws_credentials.return_value = aws_credentials

    client = boto3.client("s3", region_name=aws_credentials["aws_region"])
    client.create_bucket(Bucket=aws_credentials["bucket_name"])
    client.put_object(
        Body=b"this is text",
        Bucket=aws_credentials["bucket_name"],
        Key="/anotherfilename.txt",
    )
    response = client.list_objects_v2(Bucket=aws_credentials["bucket_name"])
    s3_contents = response.get("Contents", [])
    assert len(s3_contents)

    assert build_env.remove_s3_bucket()
    assert mock_os_popen.called
    assert mock_os_system.called
    response = client.list_objects_v2(Bucket=aws_credentials["bucket_name"])
    s3_contents = response.get("Contents", [])
    assert len(s3_contents) == 0

    mock_os_popen.return_value.read.return_value = "no db"
    assert build_env.remove_s3_bucket()


@mock.patch("os.popen")
def test_get_aws_credential_runs_successfully(mock_os_popen):
    """Tests whether AWS credentials are parsed correctly from CF"""
    build_env = BuildEnv(**DEFAULT_BUILD_ENV_SETTINGS)

    expected_result = {
        "aws_access_key_id": "ACCESS_ID_12345",
        "aws_region": "eu-west-2",
        "aws_secret_access_key": "SECRET_KEY_12345",
        "bucket_name": "BUCKET_NAME",
        "deploy_env": "",
    }

    mock_os_popen.return_value.read.return_value = """
Getting key temp_service_key for service instance s3-report-store-prototype as first.last@digital.cabinet-office.gov.uk...

{
    "aws_access_key_id": "ACCESS_ID_12345",
    "aws_region": "eu-west-2",
    "aws_secret_access_key": "SECRET_KEY_12345",
    "bucket_name": "BUCKET_NAME",
    "deploy_env": ""
}
"""

    assert build_env.get_aws_credentials() == expected_result
