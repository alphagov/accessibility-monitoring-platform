from unittest.mock import patch

from ..create_dummy_account import create_dummy_account

EXPECTED_CREATE_COMMAND: str = (
    """echo "from django.contrib.auth import get_user_model; """
    """User = get_user_model(); """
    """User.objects.create_superuser(\'EMAIL\', \'EMAIL\', \'PASSWORD\')" """
    """| python manage.py shell"""
)


@patch("os.system")
def test_create_dummy_account(mock_os_system):
    """Test create_dummy_account."""
    with patch("sys.argv", [None, "EMAIL", "PASSWORD"]):
        create_dummy_account()

    mock_os_system.assert_called_once_with(EXPECTED_CREATE_COMMAND)
