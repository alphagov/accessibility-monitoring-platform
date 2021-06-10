from helpers import (
    compile_sass_to_css,
    minify_javascript,
    recursive_copy,
)
import os

paths = {
    "static": {
        "src" : f"{os.getcwd()}/node_modules/govuk-frontend/govuk/assets",
        "dest" : f"{os.getcwd()}/accessibility_monitoring_platform/static/compiled/assets"
    },
    "css": {
        "src" : f"{os.getcwd()}/accessibility_monitoring_platform/static/scss/init.scss",
        "dest" : f"{os.getcwd()}/accessibility_monitoring_platform/static/compiled/css/init.css"
    },
    "js": {
        "src" : f"{os.getcwd()}/accessibility_monitoring_platform/static/js",
        "dest" : f"{os.getcwd()}/accessibility_monitoring_platform/static/compiled/js"
    }
}


if __name__ == "__main__":
    minify_javascript(
        src=paths["js"]["src"],
        dest=paths["js"]["dest"]
    )

    compile_sass_to_css(
        src=paths["css"]["src"],
        dest=paths["css"]["dest"]
    )

    recursive_copy(
        src=paths["static"]["src"],
        dest=paths["static"]["dest"]
    )
