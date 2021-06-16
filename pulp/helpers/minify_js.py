import glob
import os
import subprocess
import pathlib


def minify_javascript(src: str, dest: str) -> None:
    print(">>> Processing JS")
    src_files = [f for f in glob.iglob(src + "**/**", recursive=True) if os.path.isfile(f)]
    dest_files = [f for f in glob.iglob(dest + "**/**", recursive=True) if os.path.isfile(f)]
    [os.remove(path) for path in dest_files]

    for file in src_files:
        file_path = file.replace(src, "")
        js_code = f"node {pathlib.Path(__file__).parent.absolute()}/process_js.js {src}{file_path}"
        output = subprocess.check_output(
            js_code,
            shell=True
        ).decode("utf-8")
        try:
            os.makedirs("/".join(f"{dest}{file_path}".split("/")[:-1]))
        except:
            pass
        print(f"{dest}{file_path}")

        with open(f"{dest}{file_path}", "w") as outfile:
            outfile.write(output)
