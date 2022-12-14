"""check_input - Check details with user before deploying to PaaS"""
import sys
from typing import Any

from .parse_json import SettingsType


class BColours:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_prototype_settings(config: SettingsType) -> bool:
    """Formats and prints settings in config"""
    print(
        BColours.WARNING + "This script will create a new environment:" + BColours.ENDC
    )
    print("---")
    print(
        BColours.BOLD + "Copying database from: " + BColours.ENDC,
        end="",
        flush=True,
    )
    print(config["db_space_to_copy"])
    print(
        BColours.BOLD + "Copying instance from: " + BColours.ENDC,
        end="",
        flush=True,
    )
    print(config["db_instance_to_copy"])
    print(BColours.BOLD + "Creating space: " + BColours.ENDC, end="", flush=True)
    print(config["space_name"])
    print(BColours.BOLD + "Creating app: " + BColours.ENDC, end="", flush=True)
    print(config["app_name"])
    print(
        BColours.BOLD + "Creating report viewer app: " + BColours.ENDC,
        end="",
        flush=True,
    )
    print(config["report_viewer_app_name"])
    print(BColours.BOLD + "Creating database: " + BColours.ENDC, end="", flush=True)
    print(config["db_name"])
    print(BColours.BOLD + "Creating S3 bucket: " + BColours.ENDC, end="", flush=True)
    print(config["s3_report_store"])

    if config["backup_db"]:
        print(BColours.BOLD + "The database will back up to S3" + BColours.ENDC)

    return True


def check_input(args: Any, config: SettingsType):
    """Checks for user confirmation before beginning deployment to PaaS"""
    if not args.force and args.build_direction == "up":
        print_prototype_settings(config)
        while True:
            print("Do you wish to continue?:[y/n] ", end="", flush=True)
            x: str = input().lower()
            if x in ("yes", "y"):
                print(
                    BColours.OKGREEN
                    + "Building new environment in PaaS!"
                    + BColours.ENDC
                )
                break
            elif x in ("no", "n"):
                print(">>> Aborting build")
                sys.exit()

            print("Please enter yes or no")
