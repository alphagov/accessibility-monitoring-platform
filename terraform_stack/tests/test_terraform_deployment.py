from unittest.mock import patch

import pytest

from terraform_stack.terraform_deploy.terraform_deployment import get_aws_account_id


class TestGetAwsAccountId:
    """Tests for the ``get_aws_account_id`` function."""

    def test_returns_valid_aws_account_id(self):
        """It should return the AWS account ID from the STS get-caller-identity response."""
        expected_account_id = "144664177605"

        with patch(
            "terraform_stack.terraform_deploy.terraform_deployment.run"
        ) as mock_run:
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

    def test_returns_correct_account_id_for_different_accounts(self):
        """It should return different account IDs correctly when the underlying command returns them."""
        test_cases = [
            "144664177605",
            "584234429739",
            "000000000000",
            "999999999999",
        ]

        for account_id in test_cases:
            with patch(
                "terraform_stack.terraform_deploy.terraform_deployment.run"
            ) as mock_run:
                mock_run.return_value = account_id

                result = get_aws_account_id()

                assert result == account_id

    def test_run_command_structure(self):
        """It should construct the correct AWS CLI command structure."""
        with patch(
            "terraform_stack.terraform_deploy.terraform_deployment.run"
        ) as mock_run:
            mock_run.return_value = "123456789012"

            get_aws_account_id()

            expected_command = [
                "aws",
                "sts",
                "get-caller-identity",
                "--query",
                "Account",
                "--output",
                "text",
            ]
            mock_run.assert_called_once_with(
                expected_command,
                capture_output=True,
            )

    def test_returns_string_type(self):
        """It should return a string type."""
        with patch(
            "terraform_stack.terraform_deploy.terraform_deployment.run"
        ) as mock_run:
            mock_run.return_value = "144664177605"

            result = get_aws_account_id()

            assert isinstance(result, str)

    def test_raises_calledprocesserror_on_command_failure(self):
        """It should raise subprocess.CalledProcessError when the AWS CLI command fails."""
        import subprocess

        with patch(
            "terraform_stack.terraform_deploy.terraform_deployment.run"
        ) as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["aws", "sts", "get-caller-identity"],
            )

            with pytest.raises(subprocess.CalledProcessError):
                get_aws_account_id()

    def test_raises_calledprocesserror_on_client_error(self):
        """It should raise subprocess.CalledProcessError when AWS credentials are invalid."""
        import subprocess

        with patch(
            "terraform_stack.terraform_deploy.terraform_deployment.run"
        ) as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=255,
                cmd=["aws", "sts", "get-caller-identity"],
                output="Unable to locate credentials",
                stderr="Unable to locate credentials",
            )

            with pytest.raises(subprocess.CalledProcessError):
                get_aws_account_id()
