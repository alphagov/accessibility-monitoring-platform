#!/usr/bin/env python3

import argparse
import json
import os
import random
import ssl
import string
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import ClassVar, Literal, overload

import boto3
from botocore.exceptions import ClientError


@dataclass(frozen=True)
class Config:
    """Application configuration constants."""

    aws_region: str = "eu-west-2"

    aws_account_id_test: str = "144664177605"
    aws_account_id_prod: str = "584234429739"

    platform_docker_path: str = "../Dockerfiles/amp_platform.DockerFile"
    viewer_docker_path: str = "../Dockerfiles/amp_viewer.DockerFile"

    proto_terraform_bucket_store: str = "amp-stack-terraform-state"
    backup_db: str = "db-store-for-prototypes"

    create_dummy_account_script_path: str = (
        "terraform_stack/ecs_tools/create_dummy_account.py"
    )
    ecs_prepare_db_script_path: str = "terraform_stack/ecs_tools/ecs_prepare_db.py"

    @property
    def protected_s3_buckets(self) -> tuple[str, ...]:
        """Return the S3 buckets that must not be deleted."""
        return (self.proto_terraform_bucket_store,)


class Environment(StrEnum):
    PROTO = "proto"
    TEST = "test"
    STAGING = "staging"
    PROD = "prod"


class Function(StrEnum):
    UP = "up"
    DOWN = "down"
    EXEC = "exec"
    LIST = "ls"
    RESET_DB = "reset_db"
    CREATE_DUMMY_ACCOUNT = "create_dummy_account"


@dataclass(frozen=True)
class Args:
    environment: Environment
    function: Function
    command: str | None
    dryrun: bool
    force_reset_db: bool
    PROTO: ClassVar[str] = "proto"
    TEST: ClassVar[str] = "test"
    STAGING: ClassVar[str] = "staging"
    PROD: ClassVar[str] = "prod"

    @classmethod
    def parse(cls, arg_vals=None) -> "Args":
        """Create and configure the command-line argument parser.

        Returns:
            argparse.ArgumentParser: A parser configured with the supported
            deployment environment and operation.
        """
        parser = argparse.ArgumentParser(
            description="Build Docker images and deploy with Terraform."
        )

        parser.add_argument(
            "--environment",
            type=Environment,
            choices=list(Environment),
            required=True,
            help="Deployment environment",
        )

        parser.add_argument(
            "--function",
            type=Function,
            choices=list(Function),
            required=True,
            help="Operation to perform",
        )

        parser.add_argument(
            "--command",
            required=False,
            help="Command for exec function",
        )

        parser.add_argument(
            "--dryrun",
            required=False,
            action="store_true",
            help="Will list the resources it will remove if true and retain Terraform infrastructure.",
        )

        parser.add_argument(
            "--force_reset_db",
            required=False,
            action="store_true",
            help="Will reset the database when updating a prototype.",
        )

        namespace = parser.parse_args(arg_vals)

        return cls(
            environment=namespace.environment,
            function=namespace.function,
            command=namespace.command,
            dryrun=namespace.dryrun,
            force_reset_db=namespace.force_reset_db,
        )


def validate_permissions(
    args: Args,
    account_id: str,
    config: Config,
) -> None:
    """Validate that the requested operation is permitted.

    Checks that the authenticated AWS account is recognised and that the
    requested environment and operation are allowed for that account.

    Args:
        args: The parsed command-line arguments.
        account_id: The AWS account ID of the currently authenticated
            credentials.
        config: The application configuration.

    Raises:
        ValueError: If the authenticated AWS account is not recognised or the
            requested operation is not permitted for that account.
    """
    if (
        account_id != config.aws_account_id_test
        and account_id != config.aws_account_id_prod
    ):
        raise Exception(">>> You're currently signed into an unrecognised aws env")

    if account_id == config.aws_account_id_test and args.environment in [
        Environment.PROD,
        Environment.STAGING,
        Environment.TEST,
    ]:
        raise Exception(
            ">>> You're currently signed into test and launching (or decommissioning) a prod, staging, or testing env"
        )

    if account_id == config.aws_account_id_prod and args.function == "down":
        raise Exception(
            ">>> You're currently signed into prod and attempting to delete something"
        )

    if account_id == config.aws_account_id_prod and args.environment == Args.PROTO:
        raise Exception(
            ">>> You're currently signed into prod and attempting to launch a prototype"
        )

    if (
        account_id == config.aws_account_id_prod
        and args.function == "create_dummy_account"
    ):
        raise Exception(
            ">>> You're currently signed into prod and attempting to create a dummy account"
        )


@overload
def run(
    command: Sequence[str],
    *,
    capture_output: Literal[True],
    input_text: str | None = None,
) -> str: ...


@overload
def run(
    command: Sequence[str],
    *,
    capture_output: Literal[False] = False,
    input_text: str | None = None,
) -> None: ...


def run(
    command: Sequence[str],
    capture_output: bool = False,
    input_text: str | None = None,
) -> str | None:
    """Run a subprocess command.

    Args:
        command: The command and its arguments to execute.
        capture_output: If ``True``, capture and return the command's standard
            output.
        input_text: Optional text to send to the command's standard input.

    Returns:
        The command's standard output with leading and trailing whitespace
        removed if ``capture_output`` is ``True``; otherwise ``None``.

    Raises:
        subprocess.CalledProcessError: If the command exits with a non-zero
            status.
    """
    print(f"\n> {' '.join(command)}")

    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        check=True,
        capture_output=capture_output,
    )

    if capture_output:
        return result.stdout.strip()

    return None


def get_aws_account_id() -> str:
    """Return the AWS account ID for the currently authenticated credentials.

    Returns:
        The 12-digit AWS account ID associated with the active AWS CLI
        credentials.

    Raises:
        subprocess.CalledProcessError: If the AWS CLI command fails.
    """
    return run(
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


def create_proto_name() -> str:
    """Generate a prototype name based on the current Git branch.

    The prototype name consists of the ``proto_`` prefix followed by the first
    four alphanumeric characters of the current Git branch name.

    Returns:
        A prototype name derived from the current Git branch.

    Raises:
        subprocess.CalledProcessError: If the Git command fails.
    """
    git_branch_name = subprocess.check_output(
        [
            "git",
            "branch",
            "--show-current",
        ],
        text=True,
    )

    git_branch_prefix: str = "".join(
        char for char in git_branch_name if char.isalnum()
    )[:4]

    return f"proto_{git_branch_prefix}"


def create_proto_backend(
    proto_name: str,
    terraform_bucket_store: str,
) -> None:
    """Create a Terraform backend configuration file for a prototype.

    Args:
        proto_name: The name of the prototype environment.
        terraform_bucket_store: The S3 bucket used to store the Terraform
            state file.
    """
    text_file: list[str] = [
        f'bucket       = "{terraform_bucket_store}"',
        f'key          = "{proto_name}/terraform.tfstate"',
        'region       = "eu-west-2"',
        "encrypt      = true",
        "use_lockfile = true",
    ]

    backend_dir: Path = Path("backends")
    backend_dir.mkdir(parents=True, exist_ok=True)

    backend_file: Path = backend_dir / f"{proto_name}_env.hcl"
    backend_file.write_text("\n".join(text_file), encoding="utf-8")


def create_proto_env(proto_name: str) -> None:
    """Create a Terraform variables file for a prototype environment.

    Args:
        proto_name: The name of the prototype environment.
    """
    domain_friendly_proto_name: str = proto_name.replace("_", "-")

    text_file: list[str] = [
        f'environment         = "{proto_name}-env"'.replace("_", "-"),
        'domain_name         = "proto.accessibility-monitoring.service.gov.uk"',
        (
            f"app_domain_name     = "
            f'"{domain_friendly_proto_name}-amp.'
            'proto.accessibility-monitoring.service.gov.uk"'
        ),
        (
            f"app_two_domain_name = "
            f'"{domain_friendly_proto_name}-viewer.'
            'proto.accessibility-monitoring.service.gov.uk"'
        ),
        'image_tag           = "latest"',
        'viewer_image_tag    = "latest"',
    ]

    env_dir: Path = Path("envs")
    env_dir.mkdir(parents=True, exist_ok=True)

    env_file: Path = env_dir / f"{proto_name}_env_vars.tfvars"
    env_file.write_text("\n".join(text_file), encoding="utf-8")


def prepare_environment(
    args: Args,
    config: Config,
) -> str:
    """Prepare the target environment for deployment.

    For prototype environments, generates a unique environment name and
    creates the required Terraform backend and environment configuration.

    Args:
        args: The parsed command-line arguments.
        config: The application configuration.

    Returns:
        The name of the environment to operate on.
    """
    environment_name: str

    if args.environment == Environment.PROTO:
        environment_name = create_proto_name()

        print(f">>> Prototype name: {environment_name}")

        create_proto_backend(
            proto_name=environment_name,
            terraform_bucket_store=config.proto_terraform_bucket_store,
        )
        create_proto_env(environment_name)
    else:
        environment_name = args.environment

    return environment_name


def wait_for_service(
    url: str,
    timeout: int = 300,
    interval: int = 5,
) -> bool:
    """Wait for a service to become available.

    Repeatedly sends HTTP requests to the specified URL until it returns
    HTTP 200 or the timeout is reached.

    Args:
        url: The URL of the service to poll.
        timeout: The maximum number of seconds to wait.
        interval: The number of seconds to wait between requests.

    Returns:
        ``True`` if the service responds with HTTP 200.

    Raises:
        TimeoutError: If the service does not respond with HTTP 200 before
            the timeout expires.
        urllib.error.URLError: If an unrecoverable URL error occurs.
    """
    deadline: float = time.time() + timeout

    while time.time() < deadline:
        try:
            context: ssl.SSLContext = ssl._create_unverified_context()

            with urllib.request.urlopen(
                url,
                context=context,
                timeout=5,
            ) as response:
                print(f">>> {url} returned {response.status}")
                return response.status == 200

        except (urllib.error.URLError, TimeoutError) as error:
            print(error)

        time.sleep(interval)

    raise TimeoutError(f">>> {url} timed out after {timeout} seconds")


def matches(name: str, prefixes: list[str]) -> bool:
    """Return whether a string starts with any of the given prefixes.

    Args:
        name: The string to test.
        prefixes: A list of prefixes to compare against.

    Returns:
        ``True`` if ``name`` starts with at least one prefix; otherwise
        ``False``.

    Raises:
        ValueError: If ``name`` is an empty string.
    """
    if not name:
        raise ValueError("'name' must not be empty.")

    return any(name.startswith(prefix) for prefix in prefixes)


def empty_s3_bucket(
    region: str,
    prefix: str,
    dry_run: bool,
    buckets_to_ignore: tuple[str, ...],
) -> None:
    """Delete the contents of matching Amazon S3 buckets.

    Finds S3 buckets in the specified AWS region whose names begin with the
    supplied prefix. Protected buckets are skipped. If ``dry_run`` is
    ``True``, matching buckets and their object counts are listed without
    deleting any objects. Otherwise, all objects, object versions, and delete
    markers are removed from the matching bucket.

    Args:
        region: The AWS region containing the buckets.
        prefix: The bucket name prefix to match.
        dry_run: If ``True``, list matching buckets without deleting their
            contents.
        buckets_to_ignore: Bucket names that must never be modified.

    Raises:
        RuntimeError: If more than one matching bucket is found.
    """
    s3_client = boto3.client("s3", region_name=region)
    s3_resource = boto3.resource("s3", region_name=region)

    try:
        buckets: list[dict[str, object]] = s3_client.list_buckets().get("Buckets", [])

    except ClientError as error:
        print(f"[S3] Failed to list buckets: {error}")
        return

    buckets_to_delete: list[str] = []

    bucket: dict[str, object]
    for bucket in buckets:
        bucket_name: str = bucket["Name"]

        if bucket_name in buckets_to_ignore:
            print(f"[S3] Protected bucket; skipping: {bucket_name}")
            continue

        if not matches(bucket_name, [prefix]):
            continue

        print(f"[S3] Found bucket: {bucket_name}")

        try:
            bucket_region: str = (
                s3_client.get_bucket_location(
                    Bucket=bucket_name,
                ).get("LocationConstraint")
                or "us-east-1"
            )

            if bucket_region != region:
                print(f"  Skipping; bucket is in {bucket_region}, " f"not {region}")
                continue

        except ClientError as error:
            print(f"  Failed to inspect {bucket_name}: {error}")
            continue

        buckets_to_delete.append(bucket_name)

        if dry_run:
            object_count: int = sum(
                1 for _ in s3_resource.Bucket(bucket_name).objects.all()
            )
            print(f"Would delete {object_count} objects")
            continue

    if len(buckets_to_delete) > 1:
        raise RuntimeError(
            "Found more than one matching bucket; this should not happen."
        )

    if not dry_run:
        bucket_name: str

        for bucket_name in buckets_to_delete:
            try:
                s3_resource.Bucket(bucket_name).object_versions.delete()
                print(f"Deleted all objects from {bucket_name}")

            except ClientError as error:
                print(f"Failed to empty {bucket_name}: {error}")


def delete_secrets(
    region: str,
    prefix: str,
    dry_run: bool,
) -> None:
    """Delete matching AWS Secrets Manager secrets.

    Iterates over all secrets in the specified AWS region and deletes those
    whose names begin with the supplied prefix. If a secret is already
    scheduled for deletion, it is first restored before being permanently
    deleted. If ``dry_run`` is ``True``, matching secrets are listed but not
    deleted.

    Args:
        region: The AWS region containing the secrets.
        prefix: The secret name prefix to match.
        dry_run: If ``True``, list matching secrets without deleting them.

    Raises:
        botocore.exceptions.ClientError: If an AWS API request fails outside
            of the handled secret deletion errors.
    """
    sm = boto3.client("secretsmanager", region_name=region)

    paginator = sm.get_paginator("list_secrets")

    page: dict[str, object]
    for page in paginator.paginate(IncludePlannedDeletion=True):
        secrets: list[dict[str, object]] = page.get("SecretList", [])

        secret: dict[str, object]
        for secret in secrets:
            name: str = secret["Name"]

            if not matches(name, [prefix]):
                continue

            arn: str = secret["ARN"]

            print(f"[Secrets Manager] Found: {name}")

            if dry_run:
                continue

            try:
                if "DeletionDate" in secret:
                    print(f"  Scheduled for deletion; restoring first: {name}")
                    sm.restore_secret(SecretId=arn)

                sm.delete_secret(
                    SecretId=arn,
                    ForceDeleteWithoutRecovery=True,
                )

                print(f"  Force deleted: {name}")

            except ClientError as error:
                print(f"  Failed to delete {name}: {error}")


def delete_ecr_repos(
    region: str,
    prefix: str,
    dry_run: bool,
) -> None:
    """Delete matching Amazon ECR repositories.

    Iterates over all ECR repositories in the specified AWS region and deletes
    those whose names begin with the supplied prefix. If ``dry_run`` is
    ``True``, matching repositories are listed but not deleted.

    Args:
        region: The AWS region containing the repositories.
        prefix: The repository name prefix to match.
        dry_run: If ``True``, list matching repositories without deleting
            them.

    Raises:
        botocore.exceptions.ClientError: If an AWS API request fails outside
            of the handled repository deletion errors.
    """
    ecr = boto3.client("ecr", region_name=region)

    paginator = ecr.get_paginator("describe_repositories")

    page: dict[str, object]
    for page in paginator.paginate():
        repositories: list[dict[str, object]] = page.get("repositories", [])

        repo: dict[str, object]
        for repo in repositories:
            repo_name: str = repo["repositoryName"]

            if not matches(repo_name, [prefix]):
                continue

            print(f"[ECR] Found: {repo_name}")

            if dry_run:
                continue

            try:
                ecr.delete_repository(
                    repositoryName=repo_name,
                    force=True,
                )
                print(f"  Deleted: {repo_name}")

            except ClientError as error:
                print(f"  Failed to delete {repo_name}: {error}")


def flush_database() -> None:
    """Reset the application's database.

    For prototype environments, creates the required Terraform backend and
    environment configuration before initialising Terraform. Synchronises the
    backup database from the shared S3 bucket into the target environment and
    runs the database preparation script inside the ECS task.

    Raises:
        subprocess.CalledProcessError: If a Terraform, AWS CLI, or ECS Exec
            command fails.
    """
    args: Args = Args.parse()
    config: Config = Config()
    environment_name: str = prepare_environment(args=args, config=config)

    run(
        [
            "terraform",
            "init",
            f"-backend-config=backends/{environment_name}_env.hcl",
            "-reconfigure",
        ]
    )

    s3_bucket: str = get_terraform_output("s3_bucket_name")

    run(
        [
            "aws",
            "s3",
            "sync",
            f"s3://{config.backup_db}/",
            f"s3://{s3_bucket}/",
        ]
    )

    exec(f"python {config.ecs_prepare_db_script_path}")


def check_env_exists(env_name: str) -> bool:
    """Check whether the current prototype environment already exists.

    Derives the prototype environment name from the current Git branch and
    checks the available ECS clusters for a matching environment.

    Returns:
        ``True`` if a matching ECS cluster exists; otherwise ``False``.

    Raises:
        subprocess.CalledProcessError: If the AWS CLI command fails.
        json.JSONDecodeError: If the AWS CLI output is not valid JSON.
    """

    ecs_str: str = run(
        ["aws", "ecs", "list-clusters"],
        capture_output=True,
    )

    data: dict[str, list[str]] = json.loads(ecs_str)

    matching_clusters: list[str] = [
        arn for arn in data["clusterArns"] if env_name in arn
    ]

    return len(matching_clusters) > 0


def get_terraform_output(parameter: str) -> str:
    """Return the value of a Terraform output variable.

    Args:
        parameter: The name of the Terraform output variable to retrieve.

    Returns:
        The value of the specified Terraform output variable.

    Raises:
        subprocess.CalledProcessError: If the Terraform command fails.
    """
    return run(
        [
            "terraform",
            "output",
            "-raw",
            parameter,
        ],
        capture_output=True,
    )


def log_info_for_prototype() -> None:
    """Log the URLs for the prototype application and viewer.

    Retrieves the 'platform_url' and 'viewer_url' from Terraform outputs
    and prints them to the console.
    """
    url_amp: str = get_terraform_output("platform_url")
    url_viewer: str = get_terraform_output("viewer_url")
    print(f">>> amp url: {url_amp}")
    print(f">>> viewer url: {url_viewer}")


def up() -> None:
    """Build and deploy the requested environment.

    Prepares the Terraform configuration, creates the ECR repositories, builds
    and pushes the application images, and deploys the complete Terraform
    stack.

    For prototype environments only, checks whether the prototype already
    exists. After deployment, the database is prepared when the prototype is
    new or when a forced reset is requested.

    Raises:
        subprocess.CalledProcessError: If a Git, AWS CLI, Docker, or Terraform
            command exits with a non-zero status.
        TimeoutError: If a newly deployed prototype does not become available
            before the timeout expires.
    """
    args: Args = Args.parse()
    config: Config = Config()

    prototype_exists: bool = False

    if args.environment == Environment.PROTO:
        prototype_name: str = create_proto_name().replace("_", "-")
        prototype_exists = check_env_exists(prototype_name)

    environment_name: str = prepare_environment(
        args=args,
        config=config,
    )

    # Terraform init
    run(
        [
            "terraform",
            "init",
            f"-backend-config=backends/{environment_name}_env.hcl",
            "-reconfigure",
        ]
    )

    # Terraform plan
    run(["terraform", "plan", f"-var-file=envs/{environment_name}_env_vars.tfvars"])

    # Create ECR repositories only
    run(
        [
            "terraform",
            "apply",
            "-target=aws_ecr_repository.app",
            "-target=aws_ecr_repository.viewer",
            f"-var-file=envs/{environment_name}_env_vars.tfvars",
            "-auto-approve",
        ]
    )

    # Read Terraform outputs
    web_repo = get_terraform_output("web_ecr_repository_url")
    viewer_repo = get_terraform_output("viewer_ecr_repository_url")

    # Generate image tag
    git_sha = run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
    )

    image_tag = f"{git_sha}-{int(time.time())}-amd64"

    # AWS ECR login
    password = run(
        [
            "aws",
            "ecr",
            "get-login-password",
            "--region",
            config.aws_region,
        ],
        capture_output=True,
    )

    aws_account_id = get_aws_account_id()
    registry = f"{aws_account_id}.dkr.ecr.{config.aws_region}.amazonaws.com"

    run(
        [
            "docker",
            "login",
            "--username",
            "AWS",
            "--password-stdin",
            registry,
        ],
        input_text=password,
    )

    # Build web image
    print(f"\nBuilding web image: {web_repo}:{image_tag}")

    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            f"{web_repo}:{image_tag}",
            "-f",
            config.platform_docker_path,
            "--load",
            "..",
        ]
    )

    # Build viewer image
    print(f"\nBuilding viewer image: {viewer_repo}:{image_tag}")

    run(
        [
            "docker",
            "buildx",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            f"{viewer_repo}:{image_tag}",
            "-f",
            config.viewer_docker_path,
            "--load",
            "..",
        ]
    )

    # Push images
    run(["docker", "push", f"{web_repo}:{image_tag}"])
    run(["docker", "push", f"{viewer_repo}:{image_tag}"])

    # Deploy full Terraform stack
    run(
        [
            "terraform",
            "apply",
            f"-var-file=envs/{environment_name}_env_vars.tfvars",
            f"-var=image_tag={image_tag}",
            f"-var=viewer_image_tag={image_tag}",
            "-auto-approve",
        ]
    )

    print(f"\nDeployment complete.\nImage tag: {image_tag}")

    log_info_for_prototype()

    if args.environment != Environment.PROTO:
        return

    should_flush_database: bool = not prototype_exists or args.force_reset_db

    if not should_flush_database:
        return

    platform_url: str = get_terraform_output(parameter="platform_url")
    service_url: str = f"https://{platform_url}"

    wait_for_service(
        url=service_url,
        timeout=500,
    )
    flush_database()


def breakdown_proto() -> None:
    """Remove the resources associated with a prototype environment.

    Prepares the prototype environment, initialises its Terraform backend,
    retrieves the application name, and removes the associated S3 objects,
    Secrets Manager secrets, and ECR repositories.

    When dry-run mode is enabled, matching resources are listed without being
    deleted and Terraform destroy is skipped.

    Raises:
        RuntimeError: If the Terraform application name is empty.
        subprocess.CalledProcessError: If a Terraform or AWS CLI command exits
            with a non-zero status.
    """
    config: Config = Config()
    args: Args = Args.parse()

    environment_name: str = prepare_environment(
        config=config,
        args=args,
    )

    backend_file: str = f"backends/{environment_name}_env.hcl"
    variables_file: str = f"envs/{environment_name}_env_vars.tfvars"

    run(
        [
            "terraform",
            "init",
            f"-backend-config={backend_file}",
            "-reconfigure",
        ]
    )

    app_name: str = get_terraform_output("app_name")
    dry_run: bool = args.dryrun

    if not app_name:
        raise RuntimeError("Terraform output 'app_name' is blank.")

    empty_s3_bucket(
        region=config.aws_region,
        prefix=app_name,
        dry_run=dry_run,
        buckets_to_ignore=config.protected_s3_buckets,
    )

    delete_secrets(
        region=config.aws_region,
        prefix=app_name,
        dry_run=dry_run,
    )

    delete_ecr_repos(
        region=config.aws_region,
        prefix=app_name,
        dry_run=dry_run,
    )

    if dry_run:
        print(">>> Skipping Terraform destroy in dry-run mode.")
        return

    run(
        [
            "terraform",
            "destroy",
            f"-var-file={variables_file}",
            "-auto-approve",
        ]
    )


def exec(cmd: str | None = None) -> None:
    """Execute a command inside the application's running ECS task.

    Resolves the target environment, initialises the corresponding Terraform
    backend, retrieves the ECS cluster and service details, finds a running
    task, and runs the supplied command inside that task using ECS Exec.

    Args:
        cmd: The command to execute inside the ECS task. If omitted, the
            command is taken from the parsed command-line arguments.

    Raises:
        ValueError: If no command is provided.
        RuntimeError: If the target ECS service or a running ECS task cannot
            be found.
        subprocess.CalledProcessError: If a Terraform, AWS CLI, or ECS Exec
            command exits with a non-zero status.
        json.JSONDecodeError: If an AWS CLI response is not valid JSON.
    """
    args: Args = Args.parse()
    config: Config = Config()

    command: str | None = cmd if cmd is not None else args.command

    if command is None:
        raise ValueError(
            "A command must be provided either through 'cmd' or '--command'."
        )

    environment_name: str = prepare_environment(
        config=config,
        args=args,
    )
    backend_file: str = f"backends/{environment_name}_env.hcl"

    run(
        [
            "terraform",
            "init",
            f"-backend-config={backend_file}",
            "-reconfigure",
        ]
    )

    app_name = get_terraform_output("app_name")
    ecs_one_name = get_terraform_output("ecs_one_name")

    cluster_name: str = f"{app_name}-cluster"

    services_output: str = run(
        [
            "aws",
            "ecs",
            "list-services",
            "--cluster",
            cluster_name,
        ],
        capture_output=True,
    )

    services_data: dict[str, list[str]] = json.loads(services_output)
    main_ecs_name: str | None = None

    service_arn: str
    for service_arn in services_data["serviceArns"]:
        service_name: str = service_arn.split("/")[-1]

        if service_name == ecs_one_name:
            main_ecs_name = service_name
            break

    if main_ecs_name is None:
        raise RuntimeError("Could not find the target ECS service.")

    tasks_output: str = run(
        [
            "aws",
            "ecs",
            "list-tasks",
            "--cluster",
            cluster_name,
            "--service-name",
            main_ecs_name,
        ],
        capture_output=True,
    )

    tasks_data: dict[str, list[str]] = json.loads(tasks_output)
    task_arns: list[str] = tasks_data["taskArns"]

    if not task_arns:
        raise RuntimeError("Could not find a running ECS task.")

    task_arn: str = task_arns[0]
    task_id: str = task_arn.split("/")[-1]

    run(
        [
            "aws",
            "ecs",
            "execute-command",
            "--cluster",
            cluster_name,
            "--task",
            task_id,
            "--interactive",
            "--command",
            command,
        ]
    )


def list_environments() -> None:
    """List the available ECS clusters.

    Retrieves the list of ECS clusters from AWS and prints the name of each
    cluster.

    Raises:
        subprocess.CalledProcessError: If the AWS CLI command fails.
        json.JSONDecodeError: If the AWS CLI output is not valid JSON.
    """
    ecs_str: str = run(
        ["aws", "ecs", "list-clusters"],
        capture_output=True,
    )

    data: dict[str, list[str]] = json.loads(ecs_str)

    print(f'>>> Found {len(data["clusterArns"])} clusters:')

    cluster: str
    for cluster in data["clusterArns"]:
        print("- ", cluster.split("/")[-1])


def create_burner_account_terraform(
    create_account_script_path: str,
) -> None:
    """Create a dummy account by executing the helper script inside an ECS task.

    Generates a random email address and password, then uses ECS Exec to run
    the helper script inside the target ECS task. Prints the generated
    credentials on success.

    Args:
        create_account_script_path: The path to the helper script inside the
            ECS task.
    """
    print(">>> Creating burner account")

    email: str = (
        f'{"".join(random.choice(string.ascii_lowercase) for _ in range(7))}'
        "@email.com"
    )
    password: str = "".join(random.choice(string.ascii_lowercase) for _ in range(27))
    command: str = f"python {create_account_script_path} {email} {password}"

    exec(command)

    print(f"email: {email}")
    print(f"password: {password}")


def main():
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    os.chdir(project_dir)

    args = Args.parse()
    config = Config()

    account_id = get_aws_account_id()
    validate_permissions(
        args=args,
        account_id=account_id,
        config=config,
    )

    if args.function == Function.UP:
        print(">>> Deploying: ", args.environment)
        up()

    if args.function == Function.DOWN:
        print(">>> breaking down environment")
        if args.environment != Args.PROTO:
            raise Exception("Only prototypes can be broken down")
        breakdown_proto()

    if args.function == Function.EXEC:
        print(">>> exec into environment")
        exec()

    if args.function == Function.RESET_DB:
        print(">>> Resetting database")
        if args.environment != Args.PROTO:
            raise Exception("Only prototypes can have their databases reset")
        flush_database()

    if args.function == Function.LIST:
        print(">>> list environments")
        list_environments()

    if args.function == Function.CREATE_DUMMY_ACCOUNT:
        print(">>> Creating dummy account")
        if args.environment != Args.PROTO:
            raise Exception("Only prototypes can create dummy accounts")
        create_burner_account_terraform(config.create_dummy_account_script_path)


if __name__ == "__main__":
    main()
