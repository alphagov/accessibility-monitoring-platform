""" integration tests - download_webdriver - Function for downloading the Chrome webdriver"""
import platform
import os
import shutil
from typing import Any
from urllib.request import urlopen
import zipfile
from app.download_file import download_file


def download_webdriver() -> None:
    """Downloads and prepares the selenium driver"""

    webdriver_path: str = "integration_tests/chromedriver"
    if os.path.isfile(webdriver_path):
        return

    page: Any = urlopen("https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
    chrome_version: str = page.read().decode("utf-8")
    library: str = "mac64" if platform.system().lower() == "darwin" else "linux64"
    webdriver_zip: str = f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_{library}.zip"
    target_path: str = "./integration_tests/chromedriver.zip"
    download_file(url=webdriver_zip, file_name=target_path)

    target_path_unzip: str = "./integration_tests/chromedriver"
    with zipfile.ZipFile(target_path, "r") as zip_ref:
        zip_ref.extractall(target_path_unzip)

    os.rename(
        src="integration_tests/chromedriver/chromedriver",
        dst="integration_tests/chromedriver2",
    )
    shutil.rmtree(path="integration_tests/chromedriver")
    os.rename(
        src="integration_tests/chromedriver2",
        dst="integration_tests/chromedriver"
    )
    os.remove(path="integration_tests/chromedriver.zip")

    os.system(command="chmod 755 integration_tests/chromedriver")

    print(">>> chromedriver now ready")
