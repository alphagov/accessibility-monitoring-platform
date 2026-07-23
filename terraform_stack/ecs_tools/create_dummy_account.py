"""Create a dummy superuser account for the prototype.

This script creates a Django superuser by invoking the Django shell with
the email address and password supplied as command-line arguments.

Usage:
    python create_dummy_account.py <email> <password>
"""

import subprocess
import sys


def create_dummy_account() -> None:
    """Create a Django superuser from command-line arguments.

    Expects:
        sys.argv[1]: The email address for the new superuser.
        sys.argv[2]: The password for the new superuser.

    Raises:
        subprocess.CalledProcessError: If the Django shell command fails.
        IndexError: If the required command-line arguments are not provided.
    """
    temp_email: str = sys.argv[1]
    password: str = sys.argv[2]

    script: str = (
        "from django.contrib.auth import get_user_model; "
        "User = get_user_model(); "
        f"User.objects.create_superuser('{temp_email}', '{temp_email}', '{password}')"
    )

    subprocess.run(
        ["python", "manage.py", "shell"],
        input=script,
        text=True,
        check=True,
    )


if __name__ == "__main__":
    create_dummy_account()
