import io
from unittest import mock
import pytest
import os
from moto import mock_s3
import boto3

from deploy_feature_to_paas.app.parse_json import SettingsType
from deploy_feature_to_paas.app.BuildEnv import BuildEnv


data: SettingsType = {
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

FILENAME = "./requirements.txt"


def test_BuildEnv_incorrect_build_direction_raises_exception():
    with pytest.raises(Exception) as exc_info:
        BuildEnv(
            build_direction="WRONG VALUE",
            space_name=data["space_name"],
            app_name=data["app_name"],
            report_viewer_app_name=REPORT_VIEWER_APP_NAME,
            db_name=data["db_name"],
            template_object=data["template_path"],
            template_path=data["template_path"],
            manifest_path=data["temp_manifest_path"],
            temp_db_copy_path=data["temp_db_copy_path"],
            s3_report_store=data["s3_report_store"],
            db_ping_attempts=data["db_ping_attempts"],
            db_ping_interval=data["db_ping_interval"],
        )

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
def test_BuildEnv_init_raises_exception(space_name, app_name, exception):
    with pytest.raises(Exception) as exc_info:
        BuildEnv(
            build_direction="up",
            space_name=space_name,
            app_name=app_name,
            report_viewer_app_name=REPORT_VIEWER_APP_NAME,
            db_name=data["db_name"],
            template_object=data["template_path"],
            template_path=data["template_path"],
            manifest_path=data["temp_manifest_path"],
            temp_db_copy_path=data["temp_db_copy_path"],
            s3_report_store=data["s3_report_store"],
            db_ping_attempts=data["db_ping_attempts"],
            db_ping_interval=data["db_ping_interval"],
        )

    assert exception in exc_info.value.args[0]


@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.down")
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.up")
def test_BuildEnv_start_works_correctly_up(mock_buildenv_up, mock_buildenv_down):
    buildEnv = BuildEnv(
        build_direction="up",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    buildEnv.start()
    assert mock_buildenv_up.called
    assert not mock_buildenv_down.called


@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.down")
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.up")
def test_BuildEnv_start_works_correctly_down(mock_buildenv_up, mock_buildenv_down):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    buildEnv.start()
    assert not mock_buildenv_up.called
    assert mock_buildenv_down.called


@mock.patch("sys.stdout", new_callable=io.StringIO)
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.bash_command")
def test_BuildEnv_check_db_has_started_works_correctly(mock_bash_command, mock_stdout):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    mock_bash_command.return_value = True

    assert buildEnv.check_db_has_started()
    assert ">>> pinging database" in mock_stdout.getvalue()
    assert ">>> sleeping for 0 seconds" in mock_stdout.getvalue()
    assert f""">>> {data["db_name"]} started successfully""" in mock_stdout.getvalue()


@mock.patch("subprocess.Popen")
def test_BuildEnv_check_db_has_started_raises_exception(mock_popen):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    mock_popen.return_value.command.return_value = (b"", b"")

    with pytest.raises(Exception) as exc_info:
        buildEnv.check_db_has_started()

    assert "Database did not build in time limit" in exc_info.value.args[0]


@mock.patch("sys.stdout", new_callable=io.StringIO)
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.bash_command")
def test_BuildEnv_check_db_has_stopped_works_correctly(mock_bash_command, mock_stdout):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    mock_bash_command.return_value = True

    assert buildEnv.check_db_has_stopped()
    assert ">>> pinging database" in mock_stdout.getvalue()
    assert f""">>> {data["db_name"]} has been removed""" in mock_stdout.getvalue()


@mock.patch("subprocess.Popen")
def test_BuildEnv_check_db_has_stopped_raises_exception(mock_popen):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=data["template_path"],
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    mock_popen.return_value.command.return_value = (b"", b"")

    with pytest.raises(Exception) as exc_info:
        buildEnv.check_db_has_stopped()

    assert "Database could not be removed" in exc_info.value.args[0]


@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_create_manifest_completes_successfully(mock_stdout):
    template_content: str = """
        - $app_name
        - $db
        - $s3_report_store
        - $secret_key
        - $report_viewer_app_name
        - $PORT
    """
    with open(data["template_path"], "w", encoding="utf-8") as f:
        f.write(template_content)

    template_object = {
        "app_name": data["app_name"],
        "report_viewer_app_name": data["report_viewer_app_name"],
        "secret_key": "123456789",
        "db": data["db_name"],
        "s3_report_store": data["s3_report_store"],
        "PORT": "8080",
    }

    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object=template_object,
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    assert buildEnv.create_manifest()
    assert ">>> creating manifest" in mock_stdout.getvalue()

    with open(data["temp_manifest_path"], "r") as f:
        res = f.read()

    # print(res)
    assert template_object["app_name"] in res
    assert template_object["report_viewer_app_name"] in res
    assert template_object["secret_key"] in res
    assert template_object["db"] in res
    assert template_object["s3_report_store"] in res
    assert template_object["PORT"] in res

    os.remove(data["template_path"])
    os.remove(data["temp_manifest_path"])


@mock.patch("os.system")
def test_create_requirements_completes_successfully(mock_os_system):
    buildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )
    with open(FILENAME, "w") as f:
        f.write("Create a new text file!")
    mock_os_system.return_value(True)

    assert buildEnv.create_requirements()
    assert mock_os_system.called

    os.remove(FILENAME)


def test_clean_up_runs_successfully():
    with open(data["temp_manifest_path"], "w") as f:
        f.write("Create a new text file!")

    buildEnv: BuildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    assert buildEnv.clean_up()
    assert not os.path.exists(data["temp_manifest_path"])


@mock.patch("subprocess.Popen")
@mock.patch("subprocess.check_output")
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.bash_command")
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.remove_s3_bucket")
@mock.patch("sys.stdout", new_callable=io.StringIO)
def test_down_command_completes_succesfully(
    mock_stdout,
    mock_remove_s3_bucket,
    mock_bash_command,
    mock_subprocess_check_output,
    mock_popen,
):
    mock_remove_s3_bucket.return_value = True
    mock_subprocess_check_output.return_value.decode.return_value = ""
    mock_bash_command.return_value = True
    space_to_be_deleted = f">>> {data['space_name']} has been deleted"
    mock_popen.return_value.communicate.return_value = (bytes(space_to_be_deleted, 'utf-8'), b"")
    buildEnv: BuildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=1,
        db_ping_interval=0,
    )
    assert buildEnv.down()
    assert mock_bash_command.called
    assert space_to_be_deleted in mock_stdout


# @mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.bash_command")
# def test_down_command_raises_exception(mock_bash_command):

#     assert True is False


@mock.patch("os.system")
@mock.patch("os.popen")
@mock.patch("deploy_feature_to_paas.app.BuildEnv.BuildEnv.get_aws_credentials")
@mock_s3
def test_remove_s3_bucket_runs_successfully(
    mock_get_aws_credentials, mock_os_popen, mock_os_system
):
    buildEnv: BuildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )
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

    assert buildEnv.remove_s3_bucket()
    assert mock_os_popen.called
    assert mock_os_system.called
    response = client.list_objects_v2(Bucket=aws_credentials["bucket_name"])
    s3_contents = response.get("Contents", [])
    assert len(s3_contents) == 0

    mock_os_popen.return_value.read.return_value = "no db"
    assert buildEnv.remove_s3_bucket()


@mock.patch("os.popen")
def test_get_aws_credential_runs_successfully(mock_os_popen):
    buildEnv: BuildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    aws_credentials: str = """
{
    "aws_access_key_id": "ACCESS_ID_12345",
    "aws_region": "eu-west-2",
    "aws_secret_access_key": "SECRET_KEY_12345",
    "bucket_name": "BUCKET_NAME",
    "deploy_env": ""
}
    """

    expected_result = {
        "aws_access_key_id": "ACCESS_ID_12345",
        "aws_region": "eu-west-2",
        "aws_secret_access_key": "SECRET_KEY_12345",
        "bucket_name": "BUCKET_NAME",
    }

    mock_os_popen.return_value.read.return_value = aws_credentials

    assert buildEnv.get_aws_credentials() == expected_result


def test_parse_aws_credentials_runs_successfully():
    buildEnv: BuildEnv = BuildEnv(
        build_direction="down",
        space_name=data["space_name"],
        app_name=data["app_name"],
        report_viewer_app_name=REPORT_VIEWER_APP_NAME,
        db_name=data["db_name"],
        template_object={},
        template_path=data["template_path"],
        manifest_path=data["temp_manifest_path"],
        temp_db_copy_path=data["temp_db_copy_path"],
        s3_report_store=data["s3_report_store"],
        db_ping_attempts=data["db_ping_attempts"],
        db_ping_interval=data["db_ping_interval"],
    )

    aws_credentials: str = """
{
    "aws_access_key_id": "ACCESS_ID_12345",
    "aws_region": "eu-west-2",
    "aws_secret_access_key": "SECRET_KEY_12345",
    "bucket_name": "BUCKET_NAME",
    "deploy_env": ""
}
    """

    assert (
        buildEnv.parse_aws_credential(
            aws_credentials.split(),
            "aws_access_key_id",
        )
        == "ACCESS_ID_12345"
    )
