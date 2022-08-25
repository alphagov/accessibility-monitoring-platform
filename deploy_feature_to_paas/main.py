"""main - main function for deploy feature to paas"""
import argparse
from datetime import datetime
import time

from dotenv import load_dotenv
from django.core.management.utils import get_random_secret_key

from app.build_env import BuildEnv
from app.copy_db import CopyDB
from app.upload_db_to_s3 import upload_db_to_s3
from app.parse_json import (
    parse_settings_json,
    SettingsType,
)
from app.utils import (
    check_if_cf_logged_in,
    reconfigure_config_file,
)
from app.check_input import check_input


parser = argparse.ArgumentParser(description="Deploy feature branch to PaaS")

parser.add_argument(
    "-b" "--build_direction",
    dest="build_direction",
    help="Decides if it builds a branch or tears it down",
)

parser.add_argument(
    "-s" "--settings-json",
    dest="settings_json",
    help="Path for json settings",
)

parser.add_argument(
    "-f" "--force",
    type=bool,
    dest="force",
    default=False,
    help="Skip yes input",
)


def main() -> bool:
    """main function"""
    print(
        ">>> deploys_feature_to_paas creates a new environment in PaaS for testing new features"
    )
    start: float = time.time()
    args = parser.parse_args()
    config: SettingsType = parse_settings_json(args.settings_json)
    config_processed: SettingsType = reconfigure_config_file(config)
    template_object = {
        "app_name": config_processed["app_name"],
        "buildpack": "https://github.com/cloudfoundry/python-buildpack#v1.7.58",
        "report_viewer_app_name": config_processed["report_viewer_app_name"],
        "secret_key": get_random_secret_key(),
        "db": config_processed["db_name"],
        "s3_report_store": config_processed["s3_report_store"],
        "PORT": "$PORT",
    }

    check_if_cf_logged_in()

    check_input(args, config_processed)

    # raise Exception(config_processed)
    copy_db = CopyDB(
        space_name=config_processed["db_space_to_copy"],
        db_name=config_processed["db_instance_to_copy"],
        path=config_processed["temp_db_copy_path"],
    )

    if args.build_direction == "up":
        copy_db.start()

        if config_processed["backup_db"]:
            object_name = (
                "deploy_feature_to_paas_db_back/"
                f"""{datetime.now().strftime("%Y%m%dT%H%M")}"""
                f"""_{config_processed["db_space_to_copy"]}"""
                f"""_{config_processed["db_instance_to_copy"]}.sql"""
            )
            upload_db_to_s3(
                file_name=config_processed["temp_db_copy_path"],
                bucket=config_processed["s3_bucket"],
                object_name=object_name,
            )

    build_env: BuildEnv = BuildEnv(
        build_direction=args.build_direction,
        space_name=config_processed["space_name"],
        app_name=config_processed["app_name"],
        report_viewer_app_name=config_processed["report_viewer_app_name"],
        db_name=config_processed["db_name"],
        template_object=template_object,
        template_path=config_processed["template_path"],
        db_ping_attempts=config_processed["db_ping_attempts"],
        db_ping_interval=config_processed["db_ping_interval"],
        manifest_path=config_processed["temp_manifest_path"],
        temp_db_copy_path="./backup.sql",
        s3_report_store=config_processed["s3_report_store"],
    )
    build_env.start()

    if args.build_direction == "up":
        build_env.clean_up()
        copy_db.clean_up()

    end: float = time.time()
    print("Process took", end - start, "seconds")
    return True


if __name__ == "__main__":
    load_dotenv()
    main()
