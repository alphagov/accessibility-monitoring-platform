import os
import glob
from shutil import copyfile


def recursive_copy(src: str, dest: str) -> None:
    print(">>> Copying static files")
    dest_files = [
        f for f in glob.iglob(dest + "**/**", recursive=True) if os.path.isfile(f)
    ]
    dest_files_path = [s.replace(dest, "") for s in dest_files]

    src_files = [
        f for f in glob.iglob(src + "**/**", recursive=True) if os.path.isfile(f)
    ]
    src_files_path = [s.replace(src, "") for s in src_files]
    src_files_path = [s for s in src_files_path if s not in dest_files_path]

    for p in src_files_path:
        try:
            os.makedirs("/".join(f"{dest}{p}".split("/")[:-1]))
        except:
            pass
        copyfile(src=f"{src}{p}", dst=f"{dest}{p}")
