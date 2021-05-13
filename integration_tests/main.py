"""
Python script to orchestrate the integration tests
"""
import argparse
import os
import sys
import time
import platform
import shutil
import socket
from typing import Any, Union
import unittest
from unittest.runner import TextTestRunner
from unittest.result import TestResult
from unittest.suite import TestSuite
from urllib.request import urlopen
import zipfile


def ping(host: str) -> bool:
    """
    Returns True if host (str) responds to a ping request.
    """
    socket.setdefaulttimeout(23)  # timeout in seconds
    try:
        urlopen(host)
    except Exception:
        print(">>> Server did not respond")
        return False
    else:
        return True


def download_file(url: str, file_name: Union[str, None] = None) -> None:
    """ Downloads file to local dir

    Args:
        url (str): endpoint for the file you are downloading

        file_name (Union[str, None], optional): Path for file name. Defaults to None.
    """
    file_name = file_name if file_name else url.split("/")[-1]
    print(">>> Downloading webdriver")
    with urlopen(url=url) as u:
        with open(file=file_name, mode="wb") as f:
            file_size: int = int(u.info()["Content-Length"])
            file_size_dl: int = 0
            block_sz: int = 8192
            while True:
                buffer: Any = u.read(block_sz)
                if not buffer:
                    break
                file_size_dl: int = file_size_dl + len(buffer)
                f.write(buffer)
                if file_size_dl % 500 == 0:
                    percentage_complete: float = round(
                        (file_size_dl / file_size) * 100, 1
                    )
                    print(percentage_complete, "% complete", sep="")


def download_webdriver() -> None:
    """ Downloads and prepares the selenium driver """
    webdriver_path: str = "integration_tests/chromedriver"
    if os.path.isfile(webdriver_path):
        return

    library: str = "mac64" if platform.system().lower() == "darwin" else "linux64"
    webdriver_zip: str = f"https://chromedriver.storage.googleapis.com/90.0.4430.24/chromedriver_{library}.zip"
    target_path: str = "./integration_tests/chromedriver.zip"
    download_file(url=webdriver_zip, file_name=target_path)

    target_path_unzip: str = "./integration_tests/chromedriver"
    with zipfile.ZipFile(target_path, "r") as zip_ref:
        zip_ref.extractall(target_path_unzip)

    os.rename(
        src="integration_tests/chromedriver/chromedriver",
        dst="integration_tests/chromedriver2"
    )
    shutil.rmtree(path="integration_tests/chromedriver")
    os.rename(
        src="integration_tests/chromedriver2",
        dst="integration_tests/chromedriver"
    )
    os.remove(path="integration_tests/chromedriver.zip")

    os.system(command="chmod 755 integration_tests/chromedriver")

    print(">>> chromedriver now ready")


if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser(description="Starts integration tests")

    parser.add_argument("-ignore-docker", "--ignore-docker", dest="ignore_docker", action="store_true")
    options = parser.parse_args()
    os.system("pipenv lock -r > requirements.txt")
    if options.ignore_docker:
        print("Skipping docker")
    else:
        os.system("docker-compose -f docker/int_tests.docker-compose.yml down --volumes")
        os.system(
            "docker build -t django_amp_two:latest -f - . < ./docker/django_app.Dockerfile"
        )
        os.system("docker-compose -f docker/int_tests.docker-compose.yml up -d")

    download_webdriver()

    attempts: int = 0
    while True:
        if ping(host="http://0.0.0.0:8000/"):
            break
        attempts: int = attempts + 1
        if attempts > 30:
            sys.exit(1)
        time.sleep(1)

    tests_failed: bool = False
    test_suite: TestSuite = unittest.defaultTestLoader.discover(start_dir="integration_tests/", pattern="test_*.py")
    test_runner: TextTestRunner = unittest.TextTestRunner(resultclass=unittest.TextTestResult)
    res: TestResult = test_runner.run(test=test_suite)

    if not options.ignore_docker:
        os.system("docker-compose -f docker/int_tests.docker-compose.yml down")
        os.system("docker-compose -f docker/int_tests.docker-compose.yml down --volumes")

    end: float = time.time()
    print("Testing took", end - start, "seconds")

    if res.wasSuccessful():
        sys.exit(0)

    sys.exit(1)
