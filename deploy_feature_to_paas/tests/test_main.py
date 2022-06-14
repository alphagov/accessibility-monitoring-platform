from deploy_feature_to_paas.main import check_if_cf_logged_in
import pytest
from unittest import mock


@mock.patch("subprocess.Popen")
def test_check_if_cf_logged_in_return_true(mock_popen):
    successful_res_from_cf = b"""
Getting spaces in org ORGANISATION as firstname.lastname@cabinet-office.gov.uk...

name
space_name1
space_name2
"""
    mock_popen.return_value.communicate.return_value = (successful_res_from_cf, b'')
    assert check_if_cf_logged_in() is True


@mock.patch("subprocess.Popen")
def test_check_if_cf_logged_in_raise_exception(mock_popen):
    failed_res_from_cf = b"""
Getting spaces in org ORGANISATION as firstname.lastname@cabinet-office.gov.uk...

The token expired, was revoked, or the token ID is incorrect. Please log back in to re-authenticate.
FAILED    
"""
    mock_popen.return_value.communicate.return_value = (failed_res_from_cf, b'')

    with pytest.raises(Exception) as e:
        check_if_cf_logged_in()

    assert "Error not logged into CF" in str(e)
