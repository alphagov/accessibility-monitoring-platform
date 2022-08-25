"""build_env - Builds new environment in PaaS"""
import ast
import os
import re
from string import Template
import subprocess
import sys
import time
from typing import Any

import boto3


class BuildEnv:
    """BuildEnv - Builds new environment in PaaS"""

    def __init__(
        self,
        build_direction: str,
        space_name: str,
        app_name: str,
        report_viewer_app_name: str,
        db_name: str,
        template_object: Any,
        template_path: str,
        manifest_path: str,
        temp_db_copy_path: str,
        s3_report_store: str,
        db_ping_attempts: int = 20,
        db_ping_interval: int = 30,
    ):
        if build_direction != "up" and build_direction != "down":
            raise TypeError("build_direction needs to be up or down")

        if (
            space_name == "monitoring-platform-production"
            or space_name == "monitoring-platform-test"
        ):
            raise TypeError(f"{space_name} is a protected space_name")

        if (
            app_name == "accessibility-monitoring-platform-production"
            or app_name == "accessibility-monitoring-platform-test"
        ):
            raise TypeError(f"{app_name} is a protected app_name")

        self.build_direction = build_direction
        self.space_name = space_name
        self.app_name = app_name
        self.report_viewer_app_name = report_viewer_app_name
        self.db_name = db_name
        self.db_ping_attempts = db_ping_attempts
        self.db_ping_interval = db_ping_interval
        self.template_object = template_object
        self.template_path = template_path
        self.manifest_path = manifest_path
        self.temp_db_copy_path = temp_db_copy_path
        self.s3_report_store = s3_report_store

    def start(self):
        """Starts process"""
        if self.build_direction == "up":
            self.up()
        else:
            self.down()

    def check_db_has_started(self) -> bool:
        """Checks whether the db has started in PaaS"""
        attempts: int = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            try:
                self.bash_command(
                    command=f"""cf service {self.db_name}""",
                    check="succeeded",
                )
                print(f">>> {self.db_name} started successfully")
                print(f">>> sleeping for {self.db_ping_interval} seconds")
                time.sleep(self.db_ping_interval)
                return True
            except Exception:
                pass
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception("Database did not build in time limit")

    def check_db_has_stopped(self) -> bool:
        """Checks whether db has been closed correctly"""
        attempts: int = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            try:
                self.bash_command(
                    command=f"""cf service {self.db_name}""",
                    check="FAILED",
                )
                print(f">>> {self.db_name} has been removed")
                return True
            except Exception:
                pass
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception("Database could not be removed")

    def create_manifest(self) -> bool:
        """Creates cf manifest file from template and saves it to local dir"""
        print(">>> creating manifest")
        with open(self.template_path, "r", encoding="utf-8") as f:
            src: Template = Template(f.read())
            result: str = src.substitute(self.template_object)
            with open(self.manifest_path, "w", encoding="utf-8") as the_file:
                the_file.write(result)
        return True

    def create_requirements(self) -> bool:
        """Creates requirements.txt and ensures it has content"""
        while True:
            os.system("pipenv requirements > requirements.txt")
            with open("requirements.txt", "r", encoding="utf-8") as file:
                data: str = file.read().replace("\n", "")
                if len(data) > 0:
                    return True
            time.sleep(1)

    def bash_command(self, command: str, check: str) -> bool:
        """Triggers bash comamnd and checks the output

        Args:
            command (str): the bash command
            check (str): a string to check the output against

        return:
            True if it was succesful
        """
        process: subprocess.Popen = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
        )
        output: bytes = process.communicate()[0]
        if check not in output.decode("utf-8"):
            raise Exception(f"""Error during {command} - {output.decode("utf-8")}""")
        return True

    def install_conduit(self):
        """Installs conduit"""
        print(">>> Installing conduit")
        yes_pipe_process: subprocess.Popen = subprocess.Popen(
            ["yes"],
            stdout=subprocess.PIPE,
        )
        install_process: subprocess.Popen = subprocess.Popen(
            "cf install-plugin conduit".split(" "),
            stdin=yes_pipe_process.stdout,
            stdout=subprocess.PIPE,
        )
        yes_pipe_process.stdout.close()  # type: ignore
        output: bytes = install_process.communicate()[0]
        if "successfully installed" not in output.decode("utf-8"):
            raise Exception(
                f"""yes | cf install-plugin conduit - {output.decode("utf-8")}"""
            )

    def up(self) -> bool:
        """Script for creating an environment in PaaS"""
        print(">>> building environment in PaaS")
        self.create_requirements()

        print(f"cf create-space {self.space_name}")
        self.bash_command(command=f"cf create-space {self.space_name}", check="OK")

        print(f"cf target -s {self.space_name}")
        self.bash_command(
            command=f"cf target -s {self.space_name}",
            check=f"space:          {self.space_name}",
        )

        print(f"cf create-service aws-s3-bucket default {self.s3_report_store}")
        self.bash_command(
            command=f"cf create-service aws-s3-bucket default {self.s3_report_store}",
            check="OK",
        )

        print(f"cf create-service postgres tiny-unencrypted-11 {self.db_name}")
        self.bash_command(
            command=f"cf create-service postgres tiny-unencrypted-11 {self.db_name}",
            check="OK",
        )

        self.check_db_has_started()  # Checks if database has spun up correctly

        self.install_conduit()

        # Importing database into new database (first time creates db)
        os.system(f"cf conduit {self.db_name} -- psql < {self.temp_db_copy_path}")

        # Importing database into new database (second time it imports all the data)
        os.system(f"cf conduit {self.db_name} -- psql < {self.temp_db_copy_path}")

        self.create_manifest()  # Creates manifest before deloying Django app
        print(">>> pushing app to PaaS")
        subprocess.run(
            f"cf push -f {self.manifest_path} -b https://github.com/cloudfoundry/python-buildpack#v1.7.58".split(),
            stderr=sys.stderr,
            stdout=sys.stdout,
            check=True,
        )  # Deploys Django app
        print(f">>> website: {self.app_name}.london.cloudapps.digital")
        print(f">>> website: {self.report_viewer_app_name}.london.cloudapps.digital")
        return True

    def clean_up(self) -> bool:
        """Removes local files"""
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)  # Removes manifest file
        return True

    def down(self) -> bool:
        """Breaks down an environment in PaaS"""
        print(">>> breaking down environment in PaaS")

        print(f"cf target -s {self.space_name}")
        self.bash_command(
            command=f"cf target -s {self.space_name}",
            check=f"space:          {self.space_name}",
        )

        cf_apps_ls: str = subprocess.check_output("cf apps", shell=True).decode("utf-8")
        if "accessibility-monitoring-platform-test" in cf_apps_ls:
            raise Exception("The prototype build detected it may be in the testing env")

        if "accessibility-monitoring-platform-production" in cf_apps_ls:
            raise Exception(
                "The prototype build detected it may be in the production env"
            )

        attempts: int = 0
        self.remove_s3_bucket()
        while attempts < self.db_ping_attempts:
            subprocess.Popen(
                f"cf delete-space -f {self.space_name}".split(),
                stdout=subprocess.PIPE,
            )  # delete-space triggers a deletion of all apps in space

            process = subprocess.Popen(
                "cf spaces".split(),
                stdout=subprocess.PIPE,
            )  # Checks if space has been deleted
            output: bytes = process.communicate()[0]
            if self.space_name not in output.decode("utf-8"):
                print(f">>> {self.space_name} has been deleted")
                return True
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception(f"""{self.space_name} did not break down correctly""")

    def remove_s3_bucket(self) -> bool:
        """Empties and removes S3 bucket"""
        services: str = os.popen("cf services").read()
        if "aws-s3-bucket" in services:
            os.system(
                (
                    f"""cf create-service-key {self.s3_report_store}"""
                    f""" temp_service_key -c '{{"allow_external_access": true}}'"""
                )
            )
            aws_credentials = self.get_aws_credentials()

            s3_resource = boto3.resource(
                service_name="s3",
                aws_access_key_id=aws_credentials["aws_access_key_id"],
                region_name=aws_credentials["aws_region"],
                aws_secret_access_key=aws_credentials["aws_secret_access_key"],
            )

            bucket = s3_resource.Bucket(aws_credentials["bucket_name"])  # type: ignore
            bucket.objects.all().delete()

            os.system(
                f"cf delete-service-key {self.s3_report_store} temp_service_key -f"
            )
            os.system(f"cf delete-service {self.s3_report_store} -f")
        return True

    def get_aws_credentials(self):
        """Gets AWS credentials from Cloud Foundry - returns credentials as dictionary"""
        res: str = os.popen(
            f"cf service-key {self.s3_report_store} temp_service_key"
        ).read()
        clean_res = "{" + re.split("{|}", res)[1] + "}"
        return ast.literal_eval(clean_res)
