import glob
import os
from subprocess import Popen, PIPE, STDOUT
import pathlib
import os


def minify_javascript(src: str, dest: str) -> None:
    print(">>> Processing JS")
    src_files = [
        f for f in glob.iglob(src + "**/**", recursive=True) if os.path.isfile(f)
    ]

    for file in src_files:
        file_path = file.replace(src, "")
        print(file_path)
        sub_dir = file_path.split("/")
        sub_dir = "/".join(sub_dir[:-1])
        js_code = f"node {pathlib.Path(__file__).parent.absolute()}/process_js.js {src}{file_path} {dest}{sub_dir}"

        try:
            os.makedirs("/".join(f"{dest}{file_path}".split("/")[:-1]))
        except:
            pass

        stream = os.popen(js_code)
        output = stream.read()
        print(output)
