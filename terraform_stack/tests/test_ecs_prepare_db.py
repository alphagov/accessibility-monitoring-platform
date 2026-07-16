# test_ecs_prepare_db.py

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
import pytest

from terraform_stack.ecs_tools import ecs_prepare_db
from terraform_stack.ecs_tools.ecs_prepare_db import (
    delete_db,
    create_db,
    most_recent_db_s3_path,
    download_sql_file,
    load_db_backup,
    clean_up,
    redo_migrations,
    main,
)

class TestDeleteDb:
    def test_delete_db_runs_expected_command(self) -> None:
        """Run psql with the expected command and environment."""
        with patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run:
            delete_db(
                db_host="localhost",
                db_username="test_user",
                db_password="test_password",
                db_name="test_database",
            )

        mock_run.assert_called_once_with(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "test_user",
                "-d",
                "postgres",
                "-p",
                "5432",
                "-c",
                "DROP DATABASE IF EXISTS test_database;",
            ],
            env={
                **os.environ,
                "PGPASSWORD": "test_password",
            },
            check=True,
        )


    def test_delete_db_sets_pgpassword(self) -> None:
        """Override any existing PGPASSWORD environment variable."""
        with (
            patch.dict(os.environ, {"PGPASSWORD": "old_password"}),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            delete_db(
                db_host="localhost",
                db_username="test_user",
                db_password="new_password",
                db_name="test_database",
            )

        assert mock_run.call_args.kwargs["env"]["PGPASSWORD"] == "new_password"


    def test_delete_db_propagates_subprocess_error(self) -> None:
        """Propagate subprocess failures."""
        error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["psql"],
        )

        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run",
            side_effect=error,
        ):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                delete_db(
                    db_host="localhost",
                    db_username="test_user",
                    db_password="test_password",
                    db_name="test_database",
                )

        assert exc_info.value is error

class TestCreateDb:
    def test_create_db_runs_expected_psql_command(self) -> None:
        """Run psql with the expected command and connection details."""
        with (
            patch.dict(
                os.environ,
                {"EXISTING_VARIABLE": "existing_value"},
                clear=True,
            ),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            create_db(
                db_host="localhost",
                db_username="test_user",
                db_password="test_password",
                db_name="test_database",
            )

        mock_run.assert_called_once_with(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "test_user",
                "-d",
                "postgres",
                "-p",
                "5432",
                "-c",
                "CREATE DATABASE test_database;",
            ],
            env={
                "EXISTING_VARIABLE": "existing_value",
                "PGPASSWORD": "test_password",
            },
            check=True,
        )


    def test_create_db_overrides_existing_pgpassword(self) -> None:
        """Replace an existing PGPASSWORD with the supplied database password."""
        with (
            patch.dict(
                os.environ,
                {"PGPASSWORD": "old_password"},
                clear=True,
            ),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            create_db(
                db_host="database.example.com",
                db_username="database_user",
                db_password="new_password",
                db_name="application_database",
            )

        called_environment = mock_run.call_args.kwargs["env"]

        assert called_environment["PGPASSWORD"] == "new_password"


    def test_create_db_preserves_existing_environment_variables(self) -> None:
        """Pass existing environment variables to the psql subprocess."""
        with (
            patch.dict(
                os.environ,
                {
                    "PATH": "/test/bin",
                    "CUSTOM_VARIABLE": "custom_value",
                },
                clear=True,
            ),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            create_db(
                db_host="localhost",
                db_username="test_user",
                db_password="test_password",
                db_name="test_database",
            )

        called_environment = mock_run.call_args.kwargs["env"]

        assert called_environment["PATH"] == "/test/bin"
        assert called_environment["CUSTOM_VARIABLE"] == "custom_value"
        assert called_environment["PGPASSWORD"] == "test_password"


    def test_create_db_propagates_subprocess_error(self) -> None:
        """Propagate errors raised when the psql command fails."""
        process_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["psql"],
        )

        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run",
            side_effect=process_error,
        ):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                create_db(
                    db_host="localhost",
                    db_username="test_user",
                    db_password="test_password",
                    db_name="test_database",
                )

        assert exc_info.value is process_error

class TestMostRecentDbS3Path:
    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.client")
    def test_most_recent_db_s3_path_returns_latest_sql_backup(
        self,
        mock_boto_client: MagicMock,
    ) -> None:
        """Return the key of the most recently modified SQL backup."""
        s3_client = mock_boto_client.return_value
        s3_client.list_objects.return_value = {
            "Contents": [
                {
                    "Key": "backups/older.sql",
                    "LastModified": datetime(
                        2025,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
                {
                    "Key": "backups/readme.txt",
                    "LastModified": datetime(
                        2025,
                        3,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
                {
                    "Key": "backups/latest.sql",
                    "LastModified": datetime(
                        2025,
                        2,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
            ],
        }

        result = most_recent_db_s3_path("test-backup-bucket")

        assert result == "backups/latest.sql"
        mock_boto_client.assert_called_once_with("s3")
        s3_client.list_objects.assert_called_once_with(Bucket="test-backup-bucket")


    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.client")
    def test_most_recent_db_s3_path_uses_last_modified_not_list_order(
        self,
        mock_boto_client: MagicMock,
    ) -> None:
        """Select the latest backup regardless of the S3 response order."""
        s3_client = mock_boto_client.return_value
        s3_client.list_objects.return_value = {
            "Contents": [
                {
                    "Key": "backups/newest.sql",
                    "LastModified": datetime(
                        2025,
                        3,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
                {
                    "Key": "backups/oldest.sql",
                    "LastModified": datetime(
                        2025,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
                {
                    "Key": "backups/middle.sql",
                    "LastModified": datetime(
                        2025,
                        2,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
            ],
        }

        result = most_recent_db_s3_path("test-backup-bucket")

        assert result == "backups/newest.sql"


    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.client")
    def test_most_recent_db_s3_path_raises_index_error_when_no_sql_files_exist(
        self,
        mock_boto_client: MagicMock,
    ) -> None:
        """Raise IndexError when the bucket contains no SQL backups."""
        s3_client = mock_boto_client.return_value
        s3_client.list_objects.return_value = {
            "Contents": [
                {
                    "Key": "backups/readme.txt",
                    "LastModified": datetime(
                        2025,
                        1,
                        1,
                        tzinfo=timezone.utc,
                    ),
                },
            ],
        }

        with pytest.raises(IndexError):
            most_recent_db_s3_path("test-backup-bucket")


    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.client")
    def test_most_recent_db_s3_path_raises_key_error_when_contents_is_missing(
        self,
        mock_boto_client: MagicMock,
    ) -> None:
        """Raise KeyError when the S3 response has no Contents field."""
        s3_client = mock_boto_client.return_value
        s3_client.list_objects.return_value = {}

        with pytest.raises(KeyError, match="Contents"):
            most_recent_db_s3_path("test-backup-bucket")

class TestDownloadSqlFile:
    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.Session")
    def test_download_sql_file_downloads_expected_object(
        self,
        mock_session_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Download the requested S3 object to the supplied local path."""
        mock_session = mock_session_class.return_value
        mock_s3_client = mock_session.client.return_value

        download_sql_file(
            bucket="test-backup-bucket",
            s3_object="backups/latest.sql",
            local_path="/tmp/latest.sql",
        )

        mock_session_class.assert_called_once_with()
        mock_session.client.assert_called_once_with("s3")
        mock_s3_client.download_file.assert_called_once_with(
            "test-backup-bucket",
            "backups/latest.sql",
            "/tmp/latest.sql",
        )

        captured = capsys.readouterr()
        assert captured.out == f"- Downloaded backups/latest.sql\n"


    @patch("terraform_stack.ecs_tools.ecs_prepare_db.boto3.Session")
    def test_download_sql_file_propagates_download_error(
        self,
        mock_session_class: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Propagate errors raised by the S3 download operation."""
        mock_s3_client = mock_session_class.return_value.client.return_value
        download_error = ClientError(
            error_response={
                "Error": {
                    "Code": "NoSuchKey",
                    "Message": "The specified key does not exist.",
                }
            },
            operation_name="GetObject",
        )
        mock_s3_client.download_file.side_effect = download_error

        with pytest.raises(ClientError) as exc_info:
            download_sql_file(
                bucket="test-backup-bucket",
                s3_object="backups/missing.sql",
                local_path="/tmp/missing.sql",
            )

        assert exc_info.value is download_error
        assert capsys.readouterr().out == ""

class TestLoadDbBackup:
    def test_load_db_backup_runs_expected_psql_command(
        self,
        tmp_path: Path,
    ) -> None:
        """Pipe the SQL backup into psql using the supplied connection details."""
        sql_path = tmp_path / "backup.sql"
        sql_path.write_text(
            "CREATE TABLE example (id INTEGER);",
            encoding="utf-8",
        )

        with (
            patch.dict(
                os.environ,
                {"EXISTING_VARIABLE": "existing_value"},
                clear=True,
            ),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            load_db_backup(
                local_path=str(sql_path),
                db_host="localhost",
                db_username="test_user",
                db_password="test_password",
                db_name="test_database",
            )

            mock_run.assert_called_once()

            call_args = mock_run.call_args
            command = call_args.args[0]
            sql_file = call_args.kwargs["stdin"]

            assert command == [
                "psql",
                "-h",
                "localhost",
                "-U",
                "test_user",
                "-d",
                "postgres",
                "-p",
                "5432",
                "-d",
                "test_database",
            ]
            assert sql_file.name == str(sql_path)
            assert call_args.kwargs["env"] == {
                "EXISTING_VARIABLE": "existing_value",
                "PGPASSWORD": "test_password",
            }
            assert call_args.kwargs["check"] is True


    def test_load_db_backup_overrides_existing_pgpassword(
        self,
        tmp_path: Path,
    ) -> None:
        """Replace an existing PGPASSWORD with the supplied password."""
        sql_path = tmp_path / "backup.sql"
        sql_path.write_text("SELECT 1;", encoding="utf-8")

        with (
            patch.dict(
                os.environ,
                {"PGPASSWORD": "old_password"},
                clear=True,
            ),
            patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run,
        ):
            load_db_backup(
                local_path=str(sql_path),
                db_host="localhost",
                db_username="test_user",
                db_password="new_password",
                db_name="test_database",
            )

        called_environment = mock_run.call_args.kwargs["env"]

        assert called_environment["PGPASSWORD"] == "new_password"


    def test_load_db_backup_closes_sql_file_after_subprocess_finishes(
        self,
        tmp_path: Path,
    ) -> None:
        """Close the SQL file after the subprocess call completes."""
        sql_path = tmp_path / "backup.sql"
        sql_path.write_text("SELECT 1;", encoding="utf-8")

        captured_file: object | None = None

        def capture_file(*args: object, **kwargs: object) -> None:
            nonlocal captured_file
            captured_file = kwargs["stdin"]

        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run",
            side_effect=capture_file,
        ):
            load_db_backup(
                local_path=str(sql_path),
                db_host="localhost",
                db_username="test_user",
                db_password="test_password",
                db_name="test_database",
            )

        assert captured_file is not None
        assert captured_file.closed is True  # type: ignore[union-attr]


    def test_load_db_backup_raises_file_not_found_error(self) -> None:
        """Raise FileNotFoundError when the backup file does not exist."""
        with patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run:
            with pytest.raises(FileNotFoundError):
                load_db_backup(
                    local_path="/tmp/missing-backup.sql",
                    db_host="localhost",
                    db_username="test_user",
                    db_password="test_password",
                    db_name="test_database",
                )

        mock_run.assert_not_called()


    def test_load_db_backup_propagates_subprocess_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Propagate failures raised by the psql subprocess."""
        sql_path = tmp_path / "backup.sql"
        sql_path.write_text("SELECT 1;", encoding="utf-8")

        process_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["psql"],
        )

        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run",
            side_effect=process_error,
        ):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                load_db_backup(
                    local_path=str(sql_path),
                    db_host="localhost",
                    db_username="test_user",
                    db_password="test_password",
                    db_name="test_database",
                )

        assert exc_info.value is process_error

class TestCleanUp:
    def test_clean_up_deletes_file_and_prints_confirmation(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Delete the supplied file and print a confirmation message."""
        backup_path = tmp_path / "backup.sql"
        backup_path.write_text("SELECT 1;", encoding="utf-8")

        clean_up(str(backup_path))

        assert not backup_path.exists()
        assert capsys.readouterr().out == "- Deleted local DB backup\n"


    def test_clean_up_calls_os_remove_with_expected_path(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pass the supplied local path to os.remove."""
        with patch("terraform_stack.ecs_tools.ecs_prepare_db.os.remove") as mock_remove:
            clean_up("/tmp/database-backup.sql")

        mock_remove.assert_called_once_with("/tmp/database-backup.sql")
        assert capsys.readouterr().out == "- Deleted local DB backup\n"


    def test_clean_up_raises_file_not_found_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Raise FileNotFoundError when the backup file does not exist."""
        missing_path = tmp_path / "missing.sql"

        with pytest.raises(FileNotFoundError):
            clean_up(str(missing_path))

        assert capsys.readouterr().out == ""


    def test_clean_up_does_not_print_when_deletion_fails(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Do not print a success message when file deletion fails."""
        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.os.remove",
            side_effect=PermissionError("Permission denied"),
        ):
            with pytest.raises(PermissionError, match="Permission denied"):
                clean_up("/protected/database-backup.sql")

        assert capsys.readouterr().out == ""

class TestRedoMigrations:
    def test_redo_migrations_runs_expected_command(self) -> None:
        """Run the Django migrate command and check its exit status."""
        with patch("terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run") as mock_run:
            redo_migrations()

        mock_run.assert_called_once_with(
            ["python", "./manage.py", "migrate"],
            check=True,
        )


    def test_redo_migrations_propagates_subprocess_error(self) -> None:
        """Propagate an error when the migration command fails."""
        process_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["python", "./manage.py", "migrate"],
        )

        with patch(
            "terraform_stack.ecs_tools.ecs_prepare_db.subprocess.run",
            side_effect=process_error,
        ):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                redo_migrations()

        assert exc_info.value is process_error

class TestMain:
    def test_main_runs_database_restore_workflow(self) -> None:
        """Run each database restoration step with the expected arguments."""
        environment = {
            "DB_PASSWORD": ("{'username': 'test_user', 'password': 'test_password'}"),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(ecs_prepare_db, "delete_db") as mock_delete_db,
            patch.object(ecs_prepare_db, "create_db") as mock_create_db,
            patch.object(
                ecs_prepare_db,
                "most_recent_db_s3_path",
                return_value="backups/latest.sql",
            ) as mock_most_recent,
            patch.object(
                ecs_prepare_db,
                "download_sql_file",
            ) as mock_download,
            patch.object(
                ecs_prepare_db,
                "load_db_backup",
            ) as mock_load,
            patch.object(ecs_prepare_db, "clean_up") as mock_clean_up,
            patch.object(
                ecs_prepare_db,
                "redo_migrations",
            ) as mock_redo_migrations,
        ):
            main()

        database_arguments = {
            "db_host": "database.example.com",
            "db_name": "application_database",
            "db_username": "test_user",
            "db_password": "test_password",
        }

        mock_delete_db.assert_called_once_with(**database_arguments)
        mock_create_db.assert_called_once_with(**database_arguments)
        mock_most_recent.assert_called_once_with(bucket="database-backups")
        mock_download.assert_called_once_with(
            bucket="database-backups",
            s3_object="backups/latest.sql",
            local_path="temp_db.sql",
        )
        mock_load.assert_called_once_with(
            local_path="temp_db.sql",
            **database_arguments,
        )
        mock_clean_up.assert_called_once_with(local_path="temp_db.sql")
        mock_redo_migrations.assert_called_once_with()


    @pytest.mark.parametrize(
        ("missing_variable", "expected_message"),
        [
            ("DB_PASSWORD", "DB_PASSWORD is missing"),
            ("DB_HOST", "DB_HOST is missing"),
            ("DB_NAME", "DB_NAME is missing"),
            ("BUCKET_NAME", "BUCKET_NAME is missing"),
        ],
    )
    def test_main_raises_type_error_when_required_variable_is_missing(
        self,
        missing_variable: str,
        expected_message: str,
    ) -> None:
        """Raise TypeError when a required environment variable is absent."""
        environment = {
            "DB_PASSWORD": ('{"username": "test_user", "password": "test_password"}'),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }
        del environment[missing_variable]

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(ecs_prepare_db, "delete_db") as mock_delete_db,
        ):
            with pytest.raises(TypeError, match=expected_message):
                main()

        mock_delete_db.assert_not_called()


    @pytest.mark.parametrize(
        ("variable", "value", "expected_message"),
        [
            ("DB_PASSWORD", "", "DB_PASSWORD is missing"),
            ("DB_HOST", "", "DB_HOST is missing"),
            ("DB_NAME", "", "DB_NAME is missing"),
            ("BUCKET_NAME", "", "BUCKET_NAME is missing"),
        ],
    )
    def test_main_raises_type_error_when_required_variable_is_empty(
        self,
        variable: str,
        value: str,
        expected_message: str,
    ) -> None:
        """Raise TypeError when a required environment variable is empty."""
        environment = {
            "DB_PASSWORD": ('{"username": "test_user", "password": "test_password"}'),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }
        environment[variable] = value

        with patch.dict(os.environ, environment, clear=True):
            with pytest.raises(TypeError, match=expected_message):
                main()


    def test_main_raises_error_for_invalid_credentials_json(self) -> None:
        """Raise JSONDecodeError when DB_PASSWORD cannot be parsed."""
        environment = {
            "DB_PASSWORD": "not-valid-json",
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(ecs_prepare_db, "delete_db") as mock_delete_db,
        ):
            with pytest.raises(json.JSONDecodeError):
                main()

        mock_delete_db.assert_not_called()


    @pytest.mark.parametrize("missing_key", ["username", "password"])
    def test_main_raises_key_error_when_credential_field_is_missing(
        self,
        missing_key: str,
    ) -> None:
        """Raise KeyError when parsed credentials lack a required field."""
        credentials = {
            "username": "test_user",
            "password": "test_password",
        }
        del credentials[missing_key]

        environment = {
            "DB_PASSWORD": json.dumps(credentials),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(ecs_prepare_db, "delete_db") as mock_delete_db,
        ):
            with pytest.raises(KeyError, match=missing_key):
                main()

        mock_delete_db.assert_not_called()


    def test_main_stops_when_database_deletion_fails(self) -> None:
        """Stop the workflow and propagate a database deletion failure."""
        environment = {
            "DB_PASSWORD": ('{"username": "test_user", "password": "test_password"}'),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }

        process_error = subprocess.CalledProcessError(
            returncode=1,
            cmd=["psql"],
        )

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(
                ecs_prepare_db,
                "delete_db",
                side_effect=process_error,
            ),
            patch.object(ecs_prepare_db, "create_db") as mock_create_db,
            patch.object(
                ecs_prepare_db,
                "most_recent_db_s3_path",
            ) as mock_most_recent,
        ):
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                main()

        assert exc_info.value is process_error
        mock_create_db.assert_not_called()
        mock_most_recent.assert_not_called()


    def test_main_calls_workflow_functions_in_expected_order(self) -> None:
        """Run the restoration operations in the required sequence."""
        environment = {
            "DB_PASSWORD": ('{"username": "test_user", "password": "test_password"}'),
            "DB_HOST": "database.example.com",
            "DB_NAME": "application_database",
            "BUCKET_NAME": "database-backups",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch.object(ecs_prepare_db, "delete_db") as mock_delete_db,
            patch.object(ecs_prepare_db, "create_db") as mock_create_db,
            patch.object(
                ecs_prepare_db,
                "most_recent_db_s3_path",
                return_value="backups/latest.sql",
            ) as mock_most_recent,
            patch.object(
                ecs_prepare_db,
                "download_sql_file",
            ) as mock_download,
            patch.object(
                ecs_prepare_db,
                "load_db_backup",
            ) as mock_load,
            patch.object(ecs_prepare_db, "clean_up") as mock_clean_up,
            patch.object(
                ecs_prepare_db,
                "redo_migrations",
            ) as mock_redo,
        ):
            manager = pytest.MonkeyPatch()
            ordered_calls = []

            mock_delete_db.side_effect = lambda **_: ordered_calls.append("delete_db")
            mock_create_db.side_effect = lambda **_: ordered_calls.append("create_db")
            mock_most_recent.side_effect = lambda **_: (
                ordered_calls.append("most_recent_db_s3_path") or "backups/latest.sql"
            )
            mock_download.side_effect = lambda **_: ordered_calls.append(
                "download_sql_file"
            )
            mock_load.side_effect = lambda **_: ordered_calls.append("load_db_backup")
            mock_clean_up.side_effect = lambda **_: ordered_calls.append("clean_up")
            mock_redo.side_effect = lambda: ordered_calls.append("redo_migrations")

            main()
            manager.undo()

        assert ordered_calls == [
            "delete_db",
            "create_db",
            "most_recent_db_s3_path",
            "download_sql_file",
            "load_db_backup",
            "clean_up",
            "redo_migrations",
        ]
