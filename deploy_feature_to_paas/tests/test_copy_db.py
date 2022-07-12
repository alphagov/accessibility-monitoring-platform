"""test_copy_db.py - contains tests for copy_db.py"""
import io
import os
from unittest import mock

import pytest

from deploy_feature_to_paas.app.copy_db import CopyDB


SPACE_NAME = "space_name"
DB_NAME = "db_name"
PATH = "./file.sql"


@mock.patch("deploy_feature_to_paas.app.copy_db.CopyDB.copy_db")
@mock.patch("deploy_feature_to_paas.app.copy_db.CopyDB.install_conduit")
@mock.patch("deploy_feature_to_paas.app.copy_db.CopyDB.change_space")
def test_start_calls_correctly(change_space_mock, install_conduit_mock, copy_db_mock):
    """Test CopyDB.start calls correctly"""
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    copy_db.start()
    assert change_space_mock.called
    assert install_conduit_mock.called
    assert copy_db_mock.called


@mock.patch("subprocess.Popen")
def test_install_conduit_completes_correctly(mock_popen):
    """Test install conduit command completes correctly"""
    installation_return = b"""
        Plugin conduit 0.0.13 is already installed. Uninstalling existing plugin...
        OK

        Plugin conduit successfully uninstalled.
        Installing plugin conduit...
        OK

        Plugin conduit 0.0.13 successfully installed.
    """
    mock_popen.return_value.stdout = io.StringIO("")
    mock_popen.return_value.stdin = io.StringIO("")
    mock_popen.return_value.communicate.return_value = (installation_return, b"")
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    assert copy_db.install_conduit()


@mock.patch("subprocess.Popen")
def test_install_conduit_raises_exception(mock_popen):
    """Test install conduit raises exception when installation cancelled"""
    installation_return = b"Plugin installation cancelled"
    mock_popen.return_value.stdout = io.StringIO("")
    mock_popen.return_value.stdin = io.StringIO("")
    mock_popen.return_value.communicate.return_value = (installation_return, b"")
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    with pytest.raises(Exception) as exc_info:
        copy_db.install_conduit()

    assert "yes | cf install-plugin conduit -" in exc_info.value.args[0]
    assert "Plugin installation cancelled" in exc_info.value.args[0]


@mock.patch("subprocess.Popen")
def test_change_space_completes_correctly(mock_popen):
    """Test change space works correctly"""
    change_space_return = f"""
        API endpoint:   https://api.com
        API version:    3.116.0
        user:           first.last@email.com
        org:            org_name
        space:          {SPACE_NAME}
    """
    mock_popen.return_value.communicate.return_value = (
        str.encode(change_space_return),
        b"",
    )
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    assert copy_db.change_space()


@mock.patch("subprocess.Popen")
def test_copy_db_raises_exception(mock_popen):
    """Test copy_db raises exception when space is not found"""
    change_space_return = """
        Space 'fake-space' not found.
        FAILED
    """
    mock_popen.return_value.communicate.return_value = (
        str.encode(change_space_return),
        b"",
    )
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )

    with pytest.raises(Exception) as exc_info:
        copy_db.change_space()

    assert "Error during cf target -s space_name" in exc_info.value.args[0]
    assert "Space 'fake-space' not found" in exc_info.value.args[0]


@mock.patch("os.system")
def test_copy_db_completes_successfully(mock_os):
    """Test copy_db completes successfully"""
    change_space_return: str = "copies database"
    mock_os.return_value = change_space_return
    copy_db = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    assert copy_db.copy_db()
    assert mock_os.called


def test_clean_up_completes_successfully_with_file():
    """Test clean up completes with file"""
    with open(PATH, "w", encoding="utf-8") as f:
        f.write("Create a new db file!")

    copy_db: CopyDB = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    assert copy_db.clean_up()
    assert not os.path.exists(PATH)
    assert copy_db.clean_up()


def test_clean_up_completes_successfully_without_file():
    """Test clean up completes without file"""
    copy_db: CopyDB = CopyDB(
        space_name=SPACE_NAME,
        db_name=DB_NAME,
        path=PATH,
    )
    assert not os.path.exists(PATH)
    assert copy_db.clean_up()
