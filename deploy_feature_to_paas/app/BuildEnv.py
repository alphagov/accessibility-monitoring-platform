"""BuildEnv - Builds new environment in PaaS"""
import subprocess
import sys
from typing import Any, List
import time
import os
from string import Template
import boto3


class BuildEnv:
    """BuildEnv - Builds new environment in PaaS"""

    def __init__(
        self,
        build_direction: str,
        space_name: str,
        app_name: str,
        db_name: str,
        template_object: Any,
        template_path: str,
        manifest_path: str,
        backup_location: str,
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
        self.db_name = db_name
        self.db_ping_attempts = db_ping_attempts
        self.db_ping_interval = db_ping_interval
        self.template_object = template_object
        self.template_path = template_path
        self.manifest_path = manifest_path
        self.backup_location = backup_location
        self.s3_report_store = s3_report_store

    def start(self):
        """Starts process"""
        if self.build_direction == "up":
            self.up()
        else:
            self.down()

    def check_db_has_started(self):
        """Checks whether the db has started in PaaS"""
        attempts: int = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            instruction: str = f"""cf service {self.db_name}"""
            try:
                self.bash_command(command=instruction, check="succeeded")
                print(f">>> {self.db_name} started successfully")
                print(">>> sleeping for 30 seconds")
                time.sleep(30)
                return
            except:
                pass
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception("Database did not build in time limit")

    def check_db_has_stopped(self):
        """Checks whether db has been closed correctly"""
        attempts: int = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            instruction: str = f"""cf service {self.db_name}"""
            try:
                self.bash_command(command=instruction, check="FAILED")
                print(f">>> {self.db_name} has deleted")
                return
            except:
                pass
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception("Database could not be removed")

    def create_manifest(self):
        """Creates cf manifest file from template and saves it to local dir"""
        print(">>> creating manifest")
        with open(self.template_path, "r") as f:
            src: Template = Template(f.read())
            result: str = src.substitute(self.template_object)
            with open(self.manifest_path, "w") as the_file:
                the_file.write(result)

    def create_requirements(self):
        """Creates requirements.txt and ensures it has content"""
        while True:
            os.system("pipenv lock -r > requirements.txt")
            with open("requirements.txt", "r") as file:
                data: str = file.read().replace("\n", "")
                if len(data) > 0:
                    return
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
            command.split(), stdout=subprocess.PIPE
        )
        output: bytes = process.communicate()[0]
        if check not in output.decode("utf-8"):
            raise Exception(f"""Error during {command} - {output.decode("utf-8")}""")
        return True

    def install_conduit(self):
        """Installs conduit"""
        print(">>> Installing conduit")
        yes_pipe_process: subprocess.Popen = subprocess.Popen(
            ["yes"], stdout=subprocess.PIPE
        )
        install_process: subprocess.Popen = subprocess.Popen(
            "cf install-plugin conduit".split(" "),
            stdin=yes_pipe_process.stdout,
            stdout=subprocess.PIPE,
        )
        yes_pipe_process.stdout.close()  # Allow ps_process to receive a SIGPIPE if grep_process exits.
        output: bytes = install_process.communicate()[0]
        if "successfully installed" not in output.decode("utf-8"):
            raise Exception(
                f"""yes | cf install-plugin conduit - {output.decode("utf-8")}"""
            )

    def up(self):
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
        os.system(f"cf conduit {self.db_name} -- psql < {self.backup_location}")

        # Importing database into new database (second time it imports all the data)
        os.system(f"cf conduit {self.db_name} -- psql < {self.backup_location}")

        self.create_manifest()  # Creates manifest before deloying Django app
        print(">>> pushing app to PaaS")
        subprocess.run(
            f"cf push -f {self.manifest_path}".split(),
            stderr=sys.stderr,
            stdout=sys.stdout,
            check=True,
        )  # Deploys Django app
        print(f">>> website: {self.app_name}.london.cloudapps.digital")

    def clean_up(self):
        """Removes local files"""
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)  # Removes manifest

    def down(self):
        """Breaks down an environment in PaaS"""
        print(">>> breaking down environment in PaaS")
        attempts: int = 0
        self.remove_s3_bucket()
        while attempts < self.db_ping_attempts:
            process: subprocess.Popen = subprocess.Popen(
                f"cf delete-space -f {self.space_name}".split(), stdout=subprocess.PIPE
            )  # delete-space triggers a deletion of all apps in space

            process = subprocess.Popen(
                "cf spaces".split(), stdout=subprocess.PIPE
            )  # Checks if space has been deleted
            output: bytes = process.communicate()[0]
            if self.space_name not in output.decode("utf-8"):
                print(f">>> {self.space_name} has been deleted")
                return
            attempts += 1
            time.sleep(self.db_ping_interval)

        raise Exception(f"""{self.space_name} did not break down correctly""")

    def remove_s3_bucket(self) -> None:
        os.system(
            f"""cf create-service-key {self.s3_report_store} temp_service_key -c '{{"allow_external_access": true}}'"""
        )
        res: str = os.popen(f"cf service-key {self.s3_report_store} temp_service_key").read()
        services: str = os.popen("cf services").read()
        if "aws-s3-bucket" in services:
            res_split: List[str] = res.split()
            aws_access_key_id: str = self.get_aws_value(res_split, "aws_access_key_id")
            aws_region: str = self.get_aws_value(res_split, "aws_region")
            aws_secret_access_key = self.get_aws_value(res_split, "aws_secret_access_key")
            bucket_name = self.get_aws_value(res_split, "bucket_name")

            s3_resource = boto3.resource(
                service_name="s3",
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )

            bucket = s3_resource.Bucket(bucket_name)
            bucket.objects.all().delete()

            os.system(f"cf delete-service-key {self.s3_report_store} temp_service_key -f")
            os.system(f"cf delete-service {self.s3_report_store} -f")

    def get_aws_value(self, arr: List[str], substring: str) -> str:
        index: int = [idx for idx, s in enumerate(arr) if substring in s][0]
        value: str = arr[index + 1]
        value_clean: str = ''.join(c for c in value if c not in '",')
        return value_clean
