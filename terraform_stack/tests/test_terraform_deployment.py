from unittest.mock import patch

import pytest

from terraform_stack.terraform_deploy.terraform_deployment import (
    Args,
    Config,
    Environment,
    Function,
    get_aws_account_id,
    validate_permissions,
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
