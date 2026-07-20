# tests/test_create_dummy_account.py

import subprocess
from unittest.mock import Mock

import pytest

from terraform_stack.ecs_tools.create_dummy_account import create_dummy_account

import terraform_stack.ecs_tools.create_dummy_account as account_module


def test_create_dummy_account_runs_django_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the account is created using the supplied CLI arguments."""
    email = "test@example.com"
    password = "test-password"
    mock_run = Mock()

    monkeypatch.setattr(
        account_module.sys,
        "argv",
        ["create_dummy_account.py", email, password],
    )
    monkeypatch.setattr(
        account_module.subprocess,
        "run",
        mock_run,
    )

    account_module.create_dummy_account()

    expected_script = (
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        f"User.objects.create_superuser('{email}', '{email}', '{password}')"
    )

    mock_run.assert_called_once_with(
        ["python", "manage.py", "shell"],
        input=expected_script,
        text=True,
        check=True,
    )


@pytest.mark.parametrize(
    "argv",
    [
        ["create_dummy_account.py"],
        ["create_dummy_account.py", "test@example.com"],
    ],
)
def test_create_dummy_account_raises_index_error_when_arguments_are_missing(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
) -> None:
    """Test that missing command-line arguments raise an IndexError."""
    mock_run = Mock()

    monkeypatch.setattr(account_module.sys, "argv", argv)
    monkeypatch.setattr(account_module.subprocess, "run", mock_run)

    with pytest.raises(IndexError):
        account_module.create_dummy_account()

    mock_run.assert_not_called()


def test_create_dummy_account_propagates_subprocess_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that errors from the Django shell are propagated."""
    monkeypatch.setattr(
        account_module.sys,
        "argv",
        [
            "create_dummy_account.py",
            "test@example.com",
            "test-password",
        ],
    )

    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["python", "manage.py", "shell"],
    )
    mock_run = Mock(side_effect=error)

    monkeypatch.setattr(account_module.subprocess, "run", mock_run)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        account_module.create_dummy_account()

    assert exc_info.value is error
    mock_run.assert_called_once()
