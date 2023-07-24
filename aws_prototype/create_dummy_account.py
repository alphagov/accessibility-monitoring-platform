""" Create dummy account - Creates dummy account on prototype """
import os
import random
import string


def create_dummy_account(app_name: str, env_name: str) -> None:
    temp_email: str = f"""{"".join(random.choice(string.ascii_lowercase) for x in range(7))}@email.com"""
    password: str = "".join(random.choice(string.ascii_lowercase) for x in range(7))
    command: str = (
        """echo "from django.contrib.auth import get_user_model; """
        """User = get_user_model(); """
        f"""User.objects.create_superuser('{temp_email}', '{temp_email}', '{password}')" """
        """| python manage.py shell"""
    )
    copilot_exec_cmd = f"""copilot svc exec -a {app_name} -e {env_name} -n amp-svc --command "{command}" """
    os.system(copilot_exec_cmd)
    print(f"email: {temp_email}")
    print(f"password: {password}")
