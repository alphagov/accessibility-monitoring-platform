"""
Python script to orchestrate the integration tests
"""

from http.client import RemoteDisconnected
import os
import sys
import time
import unittest
import platform
from test1 import TestSum
import shutil
import socket
from urllib.request import (
    HTTPError,
    urlopen,
    URLError
)
import zipfile
from typing import Any, Union


def ping(host: str) -> bool:
    """
    Returns True if host (str) responds to a ping request.
    """
    socket.setdefaulttimeout(23)  # timeout in seconds
    try:
        urlopen(host)
    except HTTPError:
        return False
    except URLError:
        return False
    except RemoteDisconnected:
        return False
    else:
        return True


def download_file(url: str, file_name: Union[str, None] = None) -> None:
    file_name = file_name if file_name else url.split("/")[-1]
    print(">>> Downloading webdriver")
    with urlopen(url) as u:
        with open(file_name, "wb") as f:
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
                    percentage_complete: float = round((file_size_dl / file_size) * 100, 1)
                    print(percentage_complete, "% complete", sep="")


def download_selenium() -> None:
    webdriver_path: str = "integration_tests/chromedriver"
    if os.path.isfile(webdriver_path):
        return

    library: str = "mac64" if platform.system().lower() == "darwin" else "linux64"
    webdriver_zip: str = f"https://chromedriver.storage.googleapis.com/90.0.4430.24/chromedriver_{library}.zip"
    target_path: str = "./integration_tests/chromedriver.zip"
    download_file(webdriver_zip, target_path)

    target_path_unzip: str = "./integration_tests/chromedriver"
    with zipfile.ZipFile(target_path, "r") as zip_ref:
        zip_ref.extractall(target_path_unzip)

    os.rename("integration_tests/chromedriver/chromedriver", "integration_tests/chromedriver2")
    shutil.rmtree("integration_tests/chromedriver")
    os.rename("integration_tests/chromedriver2", "integration_tests/chromedriver")
    os.remove("integration_tests/chromedriver.zip")

    if library == "mac64":
        os.system("chmod 755 integration_tests/chromedriver")


if __name__ == "__main__":
    start = time.time()
    os.system("docker-compose -f docker/int_tests.docker-compose.yml down --volumes")
    os.system("docker build -t django_amp -f - . < ./docker/django_app.Dockerfile")
    os.system("docker-compose -f docker/int_tests.docker-compose.yml up -d")

    download_selenium()

    attempts: int = 0
    while True:
        if ping("http://0.0.0.0:8000/"):
            break
        attempts: int = attempts + 1
        if attempts > 30:
            sys.exit(1)
        time.sleep(1)

    tests_failed: bool = False
    try:
        unittest.main()
    except:
        tests_failed = True
        pass

    os.system("docker-compose -f docker/int_tests.docker-compose.yml down")
    os.system("docker-compose -f docker/int_tests.docker-compose.yml down --volumes")

    end: float = time.time()
    print("Testing took", end - start, "seconds")

    if tests_failed:
        sys.exit(1)
