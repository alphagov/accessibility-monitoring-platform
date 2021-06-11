import sass
import rcssmin
from typing import Any
import os


def compile_sass_to_css(src, dest):
    print(">>> Transpiling Sass")
    output: Any = sass.compile(filename=src)
    output = output.replace("/assets/", "../assets/")
    output = rcssmin.cssmin(output)
    try:
        os.makedirs("/".join(dest.split("/")[:-1]))
    except:
        pass
    with open(dest, "w") as outfile:
        outfile.write(output)
