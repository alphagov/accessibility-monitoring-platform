""" integration tests - download_file - Function for downloading file"""
from urllib.request import urlopen
from typing import Any, Union


def download_file(url: str, file_name: Union[str, None] = None) -> None:
    """Downloads file to local dir

    Args:
        url (str): endpoint for the file you are downloading
        file_name (Union[str, None], optional): Path for file name. Defaults to None.
    """
    if url[-1] == "/":
        raise Exception("URL has a trailing slash and is not a file")
    file_name = file_name if file_name else url.split("/")[-1]
    print(">>> Downloading file")
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
