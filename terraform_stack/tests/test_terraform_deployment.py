import urllib.error
from unittest.mock import MagicMock, call, patch

import pytest
from botocore.exceptions import ClientError

from terraform_stack.terraform_deploy.terraform_deployment import (
    AWS_ACCOUNT_ID_PROD,
    AWS_ACCOUNT_ID_TEST,
    PROTO_TERRAFORM_BUCKET_STORE,
    Environment,
    Function,
    check_env_exists,
    create_proto_backend,
    create_proto_env,
    create_proto_name,
    delete_ecr_repos,
    delete_secrets,
    empty_s3_bucket,
    flush_database,
    get_aws_account_id,
    get_terraform_output,
    log_info_for_prototype,
    make_parser,
    matches,
    prepare_environment,
    run,
    validate_permissions,
    wait_for_service,
)


@pytest.mark.parametrize(
    "environment,account_id",
    [(Environment.PROTO, "144664177605"), (Environment.PROD, "584234429739")],
)
def test_validate_permissions_correct_account_id(environment, account_id):
    validate_permissions(
        environment=environment,
        function=Function.LIST,
        account_id=account_id,
    )


def test_validate_permissions_unknown_account_id():
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            environment=Environment.PROTO,
            function=Function.LIST,
            account_id="unknown",
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into an unrecognised aws env"
    )


@pytest.mark.parametrize(
    "environment", [Environment.PROD, Environment.STAGING, Environment.TEST]
)
def test_validate_permissions_wrong_environment_for_test_account(environment):
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            environment=environment,
            function=Function.LIST,
            account_id=AWS_ACCOUNT_ID_TEST,
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into test and launching (or decommissioning) a prod, staging, or testing env"
    )


def test_validate_permissions_prod_drop():
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            environment=Environment.PROD,
            function=Function.DOWN,
            account_id=AWS_ACCOUNT_ID_PROD,
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into prod and attempting to delete something"
    )


def test_validate_permissions_prod_proto():
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            environment=Environment.PROTO,
            function=Function.LIST,
            account_id=AWS_ACCOUNT_ID_PROD,
        )

    assert (
        str(exc_info.value)
        == ">>> You're currently signed into prod and attempting to launch a prototype"
    )


def test_validate_permissions_prod_create_dummy_account():
    with pytest.raises(Exception) as exc_info:
        validate_permissions(
            environment=Environment.PROD,
            function=Function.CREATE_DUMMY_ACCOUNT,
            account_id=AWS_ACCOUNT_ID_PROD,
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
        proto_name: str = "proto_name"

        create_proto_backend(
            proto_name=proto_name,
            terraform_bucket_store=PROTO_TERRAFORM_BUCKET_STORE,
        )

        mock_path.assert_called_once_with("backends")
        mock_backend_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_backend_dir.__truediv__.assert_called_once_with(f"{proto_name}_env.hcl")
        mock_backend_file.write_text.assert_called_once_with(
            f"""bucket       = "{PROTO_TERRAFORM_BUCKET_STORE}"
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
def test_prepare_environment(environment, expected_environment_name):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.subprocess.check_output"
    ) as mock_check_output, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.Path"
    ) as mock_path:
        mock_check_output.return_value = "1234-branch"
        mock_backend_dir: MagicMock = MagicMock()
        mock_path.return_value = mock_backend_dir

        environment_name: str = prepare_environment(environment=environment)

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


def test_wait_for_service_timeout_error_exception():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.urllib.request.urlopen"
    ) as mock_urlopen, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.time.sleep"
    ), patch(
        "terraform_stack.terraform_deploy.terraform_deployment.ssl._create_unverified_context"
    ) as mock_create_unverified_context:
        mock_urlopen.side_effect = urllib.error.URLError("Foo")
        mock_create_unverified_context.return_value = {"ssl": "context"}
        url: str = "https://example.com"
        timeout: int = 0

        with pytest.raises(TimeoutError) as exc_info:
            wait_for_service(url=url, timeout=timeout)

        assert str(exc_info.value) == f">>> {url} timed out after {timeout} seconds"


@pytest.mark.parametrize(
    "name,prefixes,expected_result",
    [
        ("name", ["a", "b", "c"], False),
        ("name", ["am", "me"], False),
        ("name", [], False),
        ("name", ["a", "na", "c"], True),
    ],
)
def test_matches(name, prefixes, expected_result):
    assert matches(name=name, prefixes=prefixes) == expected_result


def test_matches_value_error_exception():
    with pytest.raises(ValueError) as exc_info:
        matches(name="", prefixes=[])

    assert str(exc_info.value) == "'name' must not be empty."


def test_empty_s3_bucket_client_error(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        mock_s3_client: MagicMock = MagicMock()
        mock_s3_client.list_buckets.side_effect = ClientError(
            error_response={}, operation_name="foo"
        )
        mock_s3_resource: MagicMock = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_boto3.resource.return_value = mock_s3_resource
        region: str = "eu-west-2"
        prefix: str = "prefix"

        empty_s3_bucket(
            region=region,
            prefix=prefix,
            dry_run=False,
            buckets_to_ignore=(PROTO_TERRAFORM_BUCKET_STORE,),
        )

        captured = capsys.readouterr()

        assert (
            captured.out
            == "[S3] Failed to list buckets: An error occurred (Unknown) when calling the foo operation: Unknown\n"
        )


def test_empty_s3_bucket_no_buckets(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        mock_s3_client: MagicMock = MagicMock()
        mock_s3_client.list_buckets.return_value = {"Buckets": []}
        mock_s3_resource: MagicMock = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_boto3.resource.return_value = mock_s3_resource
        region: str = "eu-west-2"
        prefix: str = "prefix"
        empty_s3_bucket(
            region=region,
            prefix=prefix,
            dry_run=False,
            buckets_to_ignore=(PROTO_TERRAFORM_BUCKET_STORE,),
        )

        captured = capsys.readouterr()

        assert captured.out == ""


def test_empty_s3_bucket_protected_bucket(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        mock_s3_client: MagicMock = MagicMock()
        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {
                    "Name": "amp-stack-terraform-state",
                    "CreationDate": "2026-04-23T22:58:21+00:00",
                    "BucketArn": "arn:aws:s3:::amp-aurora-backup-test",
                }
            ]
        }
        mock_s3_resource: MagicMock = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_boto3.resource.return_value = mock_s3_resource
        region: str = "eu-west-2"
        prefix: str = "prefix"

        empty_s3_bucket(
            region=region,
            prefix=prefix,
            dry_run=False,
            buckets_to_ignore=(PROTO_TERRAFORM_BUCKET_STORE,),
        )

        captured = capsys.readouterr()

        assert (
            captured.out
            == "[S3] Protected bucket; skipping: amp-stack-terraform-state\n"
        )


def test_delete_secrets(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        region: str = "eu-west-2"
        prefix: str = "prefix"
        mock_paginator: MagicMock = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "SecretList": [
                    {
                        "ARN": f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
                        "Name": f"{prefix}_secret_key",
                    },
                ]
            }
        ]
        mock_secrets_manager: MagicMock = MagicMock()
        mock_secrets_manager.get_paginator.return_value = mock_paginator
        mock_boto3.client.return_value = mock_secrets_manager

        delete_secrets(region=region, prefix=prefix, dry_run=False)

        captured = capsys.readouterr()

        assert (
            captured.out
            == f"[Secrets Manager] Found: {prefix}_secret_key\n  Force deleted: {prefix}_secret_key\n"
        )
        mock_secrets_manager.delete_secret.assert_called_once_with(
            SecretId=f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
            ForceDeleteWithoutRecovery=True,
        )


def test_delete_secrets_with_restore(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        region: str = "eu-west-2"
        prefix: str = "prefix"
        mock_paginator: MagicMock = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "SecretList": [
                    {
                        "ARN": f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
                        "Name": f"{prefix}_secret_key",
                        "DeletionDate": "2026-07-03T13:45:49.862000+01:00",
                    },
                ]
            }
        ]
        mock_secrets_manager: MagicMock = MagicMock()
        mock_secrets_manager.get_paginator.return_value = mock_paginator
        mock_boto3.client.return_value = mock_secrets_manager

        delete_secrets(region=region, prefix=prefix, dry_run=False)

        captured = capsys.readouterr()

        assert (
            captured.out
            == """[Secrets Manager] Found: prefix_secret_key
  Scheduled for deletion; restoring first: prefix_secret_key
  Force deleted: prefix_secret_key
"""
        )
        mock_secrets_manager.restore_secret.assert_called_once_with(
            SecretId=f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa"
        )
        mock_secrets_manager.delete_secret.assert_called_once_with(
            SecretId=f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
            ForceDeleteWithoutRecovery=True,
        )


def test_delete_secrets_with_client_error_exception(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        region: str = "eu-west-2"
        prefix: str = "prefix"
        mock_paginator: MagicMock = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "SecretList": [
                    {
                        "ARN": f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
                        "Name": f"{prefix}_secret_key",
                        "DeletionDate": "2026-07-03T13:45:49.862000+01:00",
                    },
                ]
            }
        ]
        mock_secrets_manager: MagicMock = MagicMock()
        mock_secrets_manager.get_paginator.return_value = mock_paginator
        mock_secrets_manager.delete_secret.side_effect = ClientError(
            error_response={}, operation_name="foo"
        )
        mock_boto3.client.return_value = mock_secrets_manager

        delete_secrets(region=region, prefix=prefix, dry_run=False)

        captured = capsys.readouterr()

        assert (
            captured.out
            == """[Secrets Manager] Found: prefix_secret_key
  Scheduled for deletion; restoring first: prefix_secret_key
  Failed to delete prefix_secret_key: An error occurred (Unknown) when calling the foo operation: Unknown
"""
        )
        mock_secrets_manager.restore_secret.assert_called_once_with(
            SecretId=f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa"
        )
        mock_secrets_manager.delete_secret.assert_called_once_with(
            SecretId=f"arn:aws:secretsmanager:eu-west-2:144664177605:secret:{prefix}_secret_key-urgsoa",
            ForceDeleteWithoutRecovery=True,
        )


def test_delete_ecr_repos(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        region: str = "eu-west-2"
        prefix: str = "prefix"
        mock_paginator: MagicMock = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "repositories": [
                    {"repositoryName": f"{prefix}r/amp-svc"},
                    {"repositoryName": f"{prefix}r/viewer-svc"},
                ]
            }
        ]
        mock_ecr_manager: MagicMock = MagicMock()
        mock_ecr_manager.get_paginator.return_value = mock_paginator
        mock_boto3.client.return_value = mock_ecr_manager

        delete_ecr_repos(region=region, prefix=prefix, dry_run=False)

        captured = capsys.readouterr()

        assert (
            captured.out
            == f"""[ECR] Found: {prefix}r/amp-svc
  Deleted: {prefix}r/amp-svc
[ECR] Found: {prefix}r/viewer-svc
  Deleted: {prefix}r/viewer-svc
"""
        )
        mock_ecr_manager.delete_repository.assert_has_calls(
            [
                call(repositoryName=f"{prefix}r/amp-svc", force=True),
                call(repositoryName=f"{prefix}r/viewer-svc", force=True),
            ]
        )


def test_delete_ecr_repos_client_error_exception(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.boto3"
    ) as mock_boto3:
        region: str = "eu-west-2"
        prefix: str = "prefix"
        mock_paginator: MagicMock = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "repositories": [
                    {"repositoryName": f"{prefix}r/amp-svc"},
                    {"repositoryName": f"{prefix}r/viewer-svc"},
                ]
            }
        ]
        mock_ecr_manager: MagicMock = MagicMock()
        mock_ecr_manager.get_paginator.return_value = mock_paginator
        mock_ecr_manager.delete_repository.side_effect = ClientError(
            error_response={}, operation_name="foo"
        )
        mock_boto3.client.return_value = mock_ecr_manager

        delete_ecr_repos(region=region, prefix=prefix, dry_run=False)

        captured = capsys.readouterr()

        assert (
            captured.out
            == f"""[ECR] Found: {prefix}r/amp-svc
  Failed to delete {prefix}r/amp-svc: An error occurred (Unknown) when calling the foo operation: Unknown
[ECR] Found: {prefix}r/viewer-svc
  Failed to delete {prefix}r/viewer-svc: An error occurred (Unknown) when calling the foo operation: Unknown
"""
        )
        mock_ecr_manager.delete_repository.assert_has_calls(
            [
                call(repositoryName=f"{prefix}r/amp-svc", force=True),
                call(repositoryName=f"{prefix}r/viewer-svc", force=True),
            ]
        )


def test_flush_database():
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.run"
    ) as mock_run, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.exec"
    ) as mock_exec, patch(
        "terraform_stack.terraform_deploy.terraform_deployment.get_terraform_output"
    ) as mock_get_terraform_output:
        s3_bucket_name: str = "s3_bucket_one"
        mock_get_terraform_output.return_value = s3_bucket_name

        flush_database(environment=Environment.PROD)

        mock_run.assert_has_calls(
            [
                call(
                    [
                        "terraform",
                        "init",
                        "-backend-config=backends/prod_env.hcl",
                        "-reconfigure",
                    ]
                ),
                call(
                    [
                        "aws",
                        "s3",
                        "sync",
                        "s3://db-store-for-prototypes/",
                        f"s3://{s3_bucket_name}/",
                    ]
                ),
            ]
        )
        mock_exec.assert_called_once_with(
            "python terraform_stack/ecs_tools/ecs_prepare_db.py"
        )
        mock_get_terraform_output.assert_called_once_with("s3_bucket_name")


@pytest.mark.parametrize(
    "env_name,expected_result",
    [("proto-1234", True), ("proto-none", False)],
)
def test_check_env_exists(env_name, expected_result):
    with patch("terraform_stack.terraform_deploy.terraform_deployment.run") as mock_run:
        mock_run.return_value = """{
            "clusterArns": [
                "arn:aws:ecs:eu-west-2:144664177605:cluster/app2223r-envproto-1234-Cluster-XXXXXXXXXXXX"
            ]
        }"""

        assert check_env_exists(env_name=env_name) == expected_result

        mock_run.assert_called_once_with(
            ["aws", "ecs", "list-clusters"],
            capture_output=True,
        )


def test_get_terraform_output():
    with patch("terraform_stack.terraform_deploy.terraform_deployment.run") as mock_run:
        mock_run.return_value = "terraform output result"
        parameter: str = "app_url"

        assert get_terraform_output(parameter=parameter) == "terraform output result"

        mock_run.assert_called_once_with(
            [
                "terraform",
                "output",
                "-raw",
                parameter,
            ],
            capture_output=True,
        )


def test_log_info_for_prototype(capsys):
    with patch(
        "terraform_stack.terraform_deploy.terraform_deployment.get_terraform_output"
    ) as mock_get_terraform_output:
        mock_get_terraform_output.side_effect = ["domain1", "domain2"]
        log_info_for_prototype()

        captured = capsys.readouterr()

        mock_get_terraform_output.assert_has_calls(
            [
                call("platform_url"),
                call("viewer_url"),
            ]
        )
        assert (
            captured.out
            == """>>> amp url: https://domain1
>>> viewer url: https://domain2
"""
        )


def test_make_parser():
    parsed = make_parser(
        ["--environment", Environment.PROTO, "--function", Function.UP]
    )

    assert parsed.environment == Environment.PROTO
    assert parsed.function == Function.UP
    assert parsed.command is None
    assert parsed.dryrun is False
    assert parsed.force_reset_db is False
