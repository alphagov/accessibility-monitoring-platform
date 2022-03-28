import os
import json
import sys
from .helpers import (
    compile_sass_to_css,
    minify_javascript,
    recursive_copy,
)


def pulp():
    filter_args_for_json_path = [x for x in sys.argv if ".json" in x]
    json_string = filter_args_for_json_path[0]
    with open(json_string) as json_file:
        paths = json.load(json_file)

    minify_javascript(src=paths["js"]["src"], dest=paths["js"]["dest"])

    compile_sass_to_css(src=paths["css"]["src"], dest=paths["css"]["dest"])

    recursive_copy(src=paths["static"]["src"], dest=paths["static"]["dest"])
    recursive_copy(src=paths["static_img"]["src"], dest=paths["static_img"]["dest"])
