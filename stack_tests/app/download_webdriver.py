""" integration tests - download_webdriver - Function for downloading the Chrome webdriver"""
from typing import Union
import platform
import os
import shutil
from typing import Any
from urllib.request import urlopen
import zipfile
from app.download_file import download_file


def download_webdriver(chrome_version: Union[str, None] = None) -> None:
    """Downloads and prepares the selenium driver"""
    print(">>> Change chrome_version to latest in settings to use the latest Chrome")

    webdriver_path: str = f"stack_tests/chromedriver_{chrome_version}"
    if os.path.isfile(webdriver_path):
        return

    if chrome_version == "latest":
        page: Any = urlopen("https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
        chrome_version = page.read().decode("utf-8")

    library: str = "mac64" if platform.system().lower() == "darwin" else "linux64"
    webdriver_zip: str = f"https://chromedriver.storage.googleapis.com/{chrome_version}/chromedriver_{library}.zip"
    target_path: str = "./stack_tests/chromedriver.zip"
    download_file(url=webdriver_zip, file_name=target_path)

    target_path_unzip: str = "./stack_tests/chromedriver"
    with zipfile.ZipFile(target_path, "r") as zip_ref:
        zip_ref.extractall(target_path_unzip)
    os.remove(path="stack_tests/chromedriver.zip")

    os.rename(
        src="stack_tests/chromedriver/chromedriver",
        dst="stack_tests/chromedriver2",
    )
    shutil.rmtree(path="stack_tests/chromedriver")
    os.rename(
        src="stack_tests/chromedriver2",
        dst=webdriver_path
    )

    os.system(command=f"chmod 755 {webdriver_path}")

    print(">>> chromedriver now ready")
