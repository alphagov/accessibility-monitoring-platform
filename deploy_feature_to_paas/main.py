from typing import Union
import argparse
from dotenv import load_dotenv
import time
import subprocess
import os
from django.core.management.utils import get_random_secret_key
from datetime import datetime
from app.BuildEnv import BuildEnv
from app.CopyDB import CopyDB
from app.upload_db_to_s3 import upload_db_to_s3
from app.parse_json import (
    parse_settings_json,
    SettingsType,
)
from app.check_input import check_input


parser = argparse.ArgumentParser(description="Deploy feature branch to PaaS")

parser.add_argument(
    "-b"
    "--build_direction",
    dest="build_direction",
    help="Decides if it builds a branch or tears it down"
)

parser.add_argument(
    "-s"
    "--settings-json",
    dest="settings_json",
    help="Path for json settings"
)

parser.add_argument(
    "-f"
    "--force",
    type=bool,
    dest="force",
    default=False,
    help="Skip yes input"
)


def check_if_login() -> bool:
    process = subprocess.Popen(
        "cf spaces".split(),
        stdout=subprocess.PIPE
    )
    output = process.communicate()[0]
    if "FAILED" in output.decode("utf-8"):
        raise Exception(f"""Error not logged into CF - {output.decode("utf-8")}""")
    return True


if __name__ == "__main__":
    load_dotenv()
    print(">>> deploys_feature_to_paas creates a new environment in PaaS for testing new features")
    start: float = time.time()
    args = parser.parse_args()
    config: SettingsType = parse_settings_json(args.settings_json)

    if config["space_name"] == "git_branch":
        print(">>> Creating space name from git branch")
        git_branch_name: str = subprocess.check_output(["git", "branch", "--show-current"]).decode("utf-8")
        user: Union[str, None] = os.environ.get("USER")
        user_anon: str = user[:4] if user else "unknown"
        config["space_name"] = f"{user_anon}--{git_branch_name}".replace("\n", "")
        config["app_name"] = git_branch_name.replace("\n", "")

    template_object = {
        "app_name": config["app_name"],
        "url": config["app_name"],
        "secret_key": get_random_secret_key(),
        "db": config["db_name"],
    }

    check_if_login()

    check_input(args, config)

    copy_db = CopyDB(
        space_name=config["db_space_to_copy"],
        db_name=config["db_instance_to_copy"],
        path=config["temp_db_copy_path"],
    )

    if args.build_direction == "up":
        copy_db.start()

        if config["backup_db"]:
            object_name = (
                "deploy_feature_to_paas_db_back/"
                f"""{datetime.now().strftime("%Y%m%dT%H%M")}"""
                f"""_{config["db_space_to_copy"]}"""
                f"""_{config["db_instance_to_copy"]}.sql"""
            )
            upload_db_to_s3(
                file_name=config["temp_db_copy_path"],
                bucket=config["s3_bucket"],
                object_name=object_name,
            )

    build_env: BuildEnv = BuildEnv(
        build_direction=args.build_direction,
        space_name=config["space_name"],
        app_name=config["app_name"],
        db_name=config["db_name"],
        template_object=template_object,
        template_path=config["template_path"],
        db_ping_attempts=config["db_ping_attempts"],
        db_ping_interval=config["db_ping_interval"],
        manifest_path=config["temp_db_copy_path"],
        backup_location="./backup.sql"
    )
    build_env.start()

    if args.build_direction == "up":
        build_env.clean_up()
        copy_db.clean_up()

    end: float = time.time()
    print("Process took", end - start, "seconds")
