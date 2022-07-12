"""utils - contains utility functions used in deploy_feature_to_paas app"""
import os
import subprocess
from typing import Union

from .parse_json import SettingsType


def check_if_cf_logged_in() -> bool:
    """Checks if logged into cloud foundry. Returns True if logged in"""
    process: subprocess.Popen = subprocess.Popen(
        "cf spaces".split(),
        stdout=subprocess.PIPE,
    )
    output = process.communicate()[0]
    decoded_output: str = output.decode("utf-8")
    if "FAILED" in decoded_output:
        raise Exception(f"""Error not logged into CF - {decoded_output}""")
    return True


def reconfigure_config_file(config: SettingsType) -> SettingsType:
    """Takes config file and produces settings"""
    git_branch_name: str = subprocess.check_output(
        [
            "git",
            "branch",
            "--show-current",
        ]
    ).decode("utf-8")
    user: Union[str, None] = os.environ.get("USER")
    user_anon: str = user[:4] if user else "unknown"

    if config["space_name"] == "git_branch":
        print(">>> Creating space name from git branch")
        config["space_name"] = f"{user_anon}--{git_branch_name}".replace("\n", "")

    if config["app_name"] == "git_branch":
        print(">>> Creating app name from git branch")
        config["app_name"] = git_branch_name.replace("\n", "")

    if config["report_viewer_app_name"] == "git_branch":
        print(">>> Creating report viewer app name from git branch")
        config["report_viewer_app_name"] = f"""{config["app_name"]}-report-viewer"""
    return config
