from .helpers import (
    compile_sass_to_css,
    minify_javascript,
    recursive_copy,
)
import os

paths = {
    "static": {
        "src": "./node_modules/govuk-frontend/govuk/assets",
        "dest": "./accessibility_monitoring_platform/static/compiled/assets",
    },
    "css": {
        "src": "./accessibility_monitoring_platform/static/scss/init.scss",
        "dest": "./accessibility_monitoring_platform/static/compiled/css/init.css",
    },
    "js": {
        "src": "./accessibility_monitoring_platform/static/js",
        "dest": "./accessibility_monitoring_platform/static/compiled/js",
    },
}


def pulp():
    minify_javascript(src=paths["js"]["src"], dest=paths["js"]["dest"])

    compile_sass_to_css(src=paths["css"]["src"], dest=paths["css"]["dest"])

    recursive_copy(src=paths["static"]["src"], dest=paths["static"]["dest"])
