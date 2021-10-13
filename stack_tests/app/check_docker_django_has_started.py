""" integration tests - check_docker_django_has_started - Function for checking whether django has started correctly"""

import time
from app.ping import ping


def check_docker_django_has_started(max_attempts: int, endpoint: str) -> None:
    """Checks whether the django has started correctly in the docker container

    Args:
        endpoint (str): Endpoint to check if live
    """
    attempts: int = 0
    while True:
        if ping(host=endpoint):
            break
        attempts: int = attempts + 1
        if attempts > max_attempts:
            raise Exception("Could not connect to Docker container")
        time.sleep(1)
