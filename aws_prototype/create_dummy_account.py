""" Create dummy account - Creates dummy account on prototype """
import os
import sys


def create_dummy_account() -> None:
    temp_email: str = sys.argv[1]
    password: str = sys.argv[2]

    command: str = (
        """echo "from django.contrib.auth import get_user_model; """
        """User = get_user_model(); """
        f"""User.objects.create_superuser('{temp_email}', '{temp_email}', '{password}')" """
        """| python manage.py shell"""
    )
    os.system(command)


if __name__ == "__main__":
    create_dummy_account()
