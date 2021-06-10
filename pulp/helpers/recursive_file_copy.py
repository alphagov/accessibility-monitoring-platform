import os
from pathlib import Path
import glob
from shutil import copyfile


def recursive_copy(src: str, dest: str) -> None:
    print(">>> Copying static files")
    dest_files = [f for f in glob.iglob(dest + '**/**', recursive=True) if os.path.isfile(f)]
    dest_files_path = [s.replace(dest, '') for s in dest_files]

    src_files = [f for f in glob.iglob(src + '**/**', recursive=True) if os.path.isfile(f)]
    src_files_path = [s.replace(src, '') for s in src_files]
    src_files_path = [s for s in src_files_path if s not in dest_files_path]
    [copyfile(src=f'{src}{f}', dst=f'{dest}{f}') for f in src_files_path]
