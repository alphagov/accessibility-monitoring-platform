import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from terraform_stack.terraform_deploy.terraform_deployment import (
    Args,
    Config,
    Environment,
    Function,
    create_proto_backend,
    create_proto_env,
    create_proto_name,
    get_aws_account_id,
    prepare_environment,
    run,
    validate_permissions,
    wait_for_service,
)


def test_config():
    config: Config = Config()

    assert config.aws_region == "eu-west-2"
    assert config.aws_account_id_test == "144664177605"
    assert config.aws_account_id_prod == "584234429739"
    assert config.platform_docker_path == "../Dockerfiles/amp_platform.DockerFile"
    assert config.viewer_docker_path == "../Dockerfiles/amp_viewer.DockerFile"
    assert config.proto_terraform_bucket_store == "amp-stack-terraform-state"
    assert config.backup_db == "db-store-for-prototypes"
    assert (
        config.create_dummy_account_script_path
        == "terraform_stack/ecs_tools/create_dummy_account.py"
    )
    assert (
        config.ecs_prepare_db_script_path
        == "terraform_stack/ecs_tools/ecs_prepare_db.py"
    )
    assert config.protected_s3_buckets == (config.proto_terraform_bucket_store,)


def test_args_parse():
    args_parse: Args = Args.parse(
        ["--environment", Environment.PROTO, "--function", Function.UP]
    )

    assert args_parse.environment == Environment.PROTO
    assert args_parse.function == Function.UP
    assert args_parse.command is None
    assert args_parse.dryrun is False
    assert args_parse.force_reset_db is False


@pytest.mark.parametrize(
    "environment,account_id",
    [(Environment.PROTO, "144664177605"), (Environment.PROD, "584234429739")],
)
def test_validate_permissions_correct_account_id(environment, account_id):
    mock_args: Args = Args.parse(
        ["--environment", environment, "--function", Function.LIST]
    )
    config: Config = Config()
    validate_permissions(args=mock_args, account_id=account_id, config=config)


def test_validate_permissions_unknown_account_id():
    mock_args: Args = Args.parse(
        ["--environment", Environment.PROTO, "--function", Function.LIST]
    )
    config: Config = Config()
    with pytest.raises(Exception) as exc_info:
        validate_permissions(args=mock_args, account_id="unknown", config=config)

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into an unrecognised aws env"
    )


@pytest.mark.parametrize(
    "environment", [Environment.PROD, Environment.STAGING, Environment.TEST]
)
def test_validate_permissions_wrong_environment_for_test_account(environment):
    mock_args: Args = Args.parse(
        ["--environment", environment, "--function", Function.LIST]
    )
    config: Config = Config()
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            args=mock_args, account_id=config.aws_account_id_test, config=config
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into test and launching (or decommissioning) a prod, staging, or testing env"
    )


def test_validate_permissions_prod_drop():
    mock_args: Args = Args.parse(
        ["--environment", Environment.PROD, "--function", Function.DOWN]
    )
    config: Config = Config()
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            args=mock_args, account_id=config.aws_account_id_prod, config=config
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into prod and attempting to delete something"
    )


def test_validate_permissions_prod_proto():
    mock_args: Args = Args.parse(
        ["--environment", Environment.PROTO, "--function", Function.LIST]
    )
    config: Config = Config()
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            args=mock_args, account_id=config.aws_account_id_prod, config=config
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into prod and attempting to launch a prototype"
    )


def test_validate_permissions_prod_create_dummy_account():
    mock_args: Args = Args.parse(
        [
            "--environment",
            Environment.PROD,
            "--function",
            Function.CREATE_DUMMY_ACCOUNT,
        ]
    )
    config: Config = Config()
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            args=mock_args, account_id=config.aws_account_id_prod, config=config
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into prod and attempting to create a dummy account"
    )


@pytest.mark.parametrize(
    "command,capture_output,input_text,expected_result",
    [
        (["echo", "foo"], False, None, None),
        (["echo", "foo"], False, "bar", None),
        (["echo", "foo"], True, None, "foo"),
        (["echo", "foo"], True, "bar", "foo"),
    ],
)
def test_run_command_capture_output(
    command, capture_output, input_text, expected_result
):
    result: str | None = run(
        command=command, capture_output=capture_output, input_text=input_text
    )

    assert result == expected_result


def test_run_passes_input_to_subprocess_run():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.subprocess.run"
    ) as mock_run:
        run(command=["echo", "foo"], capture_output=True, input_text="bar")

        mock_run.assert_called_once_with(
            [
                "echo",
                "foo",
            ],
            input="bar",
            text=True,
            check=True,
            capture_output=True,
        )


def test_get_aws_account_id():
    expected_account_id = "144664177605"

    with patch("terraform_stack.terraform_deploy.terraform_deployment.run") as mock_run:
        mock_run.return_value = expected_account_id

        result = get_aws_account_id()

        mock_run.assert_called_once_with(
            [
                "aws",
                "sts",
                "get-caller-identity",
                "--query",
                "Account",
                "--output",
                "text",
            ],
            capture_output=True,
        )
        assert result == expected_account_id


@pytest.mark.parametrize(
    "git_branch_name,expected_proto_name",
    [("1234-branch", "proto_1234"), ("dev-branch", "proto_devb")],
)
def test_create_proto_name(git_branch_name, expected_proto_name):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.subprocess.check_output"
    ) as mock_check_output:
        mock_check_output.return_value = git_branch_name

        result = create_proto_name()

        mock_check_output.assert_called_once_with(
            [
                "git",
                "branch",
                "--show-current",
            ],
            text=True,
        )
        assert result == expected_proto_name


def test_create_proto_backend():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.Path"
    ) as mock_path:
        mock_backend_file: MagicMock = MagicMock()
        mock_backend_dir: MagicMock = MagicMock()
        mock_backend_dir.__truediv__.return_value = mock_backend_file
        mock_path.return_value = mock_backend_dir
        config: Config = Config()
        proto_name: str = "proto_name"

        create_proto_backend(
            proto_name=proto_name,
            terraform_bucket_store=config.proto_terraform_bucket_store,
        )

        mock_path.assert_called_once_with("backends")
        mock_backend_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_backend_dir.__truediv__.assert_called_once_with(f"{proto_name}_env.hcl")
        mock_backend_file.write_text.assert_called_once_with(
            f"""bucket       = "{config.proto_terraform_bucket_store}"
key          = "{proto_name}/terraform.tfstate"
region       = "eu-west-2"
encrypt      = true
use_lockfile = true""",
            encoding="utf-8",
        )


def test_create_proto_env():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.Path"
    ) as mock_path:
        mock_backend_file: MagicMock = MagicMock()
        mock_backend_dir: MagicMock = MagicMock()
        mock_backend_dir.__truediv__.return_value = mock_backend_file
        mock_path.return_value = mock_backend_dir
        proto_name: str = "proto_name"

        create_proto_env(proto_name=proto_name)

        mock_path.assert_called_once_with("envs")
        mock_backend_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_backend_dir.__truediv__.assert_called_once_with(
            f"{proto_name}_env_vars.tfvars"
        )
        mock_backend_file.write_text.assert_called_once_with(
            '''environment         = "proto-name-env"
domain_name         = "proto.accessibility-monitoring.service.gov.uk"
app_domain_name     = "proto-name-amp.proto.accessibility-monitoring.service.gov.uk"
app_two_domain_name = "proto-name-viewer.proto.accessibility-monitoring.service.gov.uk"
image_tag           = "latest"
viewer_image_tag    = "latest"''',
            encoding="utf-8",
        )


@pytest.mark.parametrize(
    "environment,expected_environment_name",
    [
        (Environment.PROD, "prod"),
        (Environment.PROTO, "proto_1234"),
        (Environment.STAGING, "staging"),
        (Environment.TEST, "test"),
    ],
)
@pytest.mark.parametrize(
    "function",
    [
        Function.CREATE_DUMMY_ACCOUNT,
        Function.DOWN,
        Function.EXEC,
        Function.LIST,
        Function.RESET_DB,
        Function.UP,
    ],
)
def test_prepare_environment(function, environment, expected_environment_name):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.subprocess.check_output"
    ) as mock_check_output, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.Path"
    ) as mock_path:
        mock_check_output.return_value = "1234-branch"
        mock_backend_dir: MagicMock = MagicMock()
        mock_path.return_value = mock_backend_dir
        mock_args: Args = Args.parse(
            ["--environment", environment, "--function", function]
        )
        config: Config = Config()

        environment_name: str = prepare_environment(args=mock_args, config=config)

        assert environment_name == expected_environment_name


def test_wait_for_service_immediate_success():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.urllib.request.urlopen"
    ) as mock_urlopen, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.time.sleep"
    ) as mock_sleep, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.ssl._create_unverified_context"
    ) as mock_create_unverified_context:
        mock_create_unverified_context.return_value = {"ssl": "context"}
        wait_for_service(url="https://example.com")

        mock_urlopen.assert_called_once_with(
            "https://example.com", context={"ssl": "context"}, timeout=5
        )
        mock_sleep.assert_not_called()


def test_wait_for_service_timeout():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.urllib.request.urlopen"
    ) as mock_urlopen, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.time.sleep"
    ) as mock_sleep, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.ssl._create_unverified_context"
    ) as mock_create_unverified_context:
        mock_urlopen.side_effect = urllib.error.URLError("Foo")
        mock_create_unverified_context.return_value = {"ssl": "context"}
        url: str = "https://example.com"
        timeout: int = 0

        with pytest.raises(TimeoutError) as exc_info:
            wait_for_service(url=url, timeout=timeout)

        assert str(exc_info.value) == f">>> {url} timed out after {timeout} seconds"
        # mock_urlopen.assert_not_called()
        # mock_sleep.assert_not_called()
