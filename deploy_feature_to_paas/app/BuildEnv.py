import subprocess
import sys
from typing import Any
import time
import os
from string import Template


class BuildEnv:
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
        db_ping_attempts: int = 20,
        db_ping_interval: int = 30,
    ):
        if (
            build_direction != "up"
            and build_direction != "down"
        ):
            raise TypeError("build_direction needs to be up or down")
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

    def start(self):
        if self.build_direction == "up":
            self.up()
        else:
            self.down()

    def check_db_has_started(self):
        attempts = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            instruction = f"""cf service {self.db_name}"""
            try:
                self.bash_command(
                    command=instruction,
                    check="succeeded"
                )
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
        attempts = 0
        while attempts < self.db_ping_attempts:
            print(">>> pinging database")
            instruction = f"""cf service {self.db_name}"""
            try:
                self.bash_command(
                    command=instruction,
                    check="FAILED"
                )
                print(f">>> {self.db_name} has deleted")
                return
            except:
                pass
            attempts += 1
            time.sleep(self.db_ping_interval)
        raise Exception("Database could not be removed")

    def create_manifest(self):
        print(">>> creating manifest")
        with open(self.template_path, "r") as f:
            src = Template(f.read())
            result = src.substitute(self.template_object)
            with open(self.manifest_path, "w") as the_file:
                the_file.write(result)

    def create_requirements(self):
        # Creates requirements.txt for PaaS
        while True:
            os.system("pipenv lock -r > requirements.txt")
            with open("requirements.txt", "r") as file:
                data = file.read().replace("\n", "")
                if len(data) > 0:
                    return
            time.sleep(1)

    def bash_command(self, command: str, check: str):
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE
        )
        output = process.communicate()[0]
        if check not in output.decode("utf-8"):
            raise Exception(f"""Error during {command} - {output.decode("utf-8")}""")
        return True

    def up(self):
        print(">>> building environment in PaaS")
        self.create_requirements()

        instructions = [
            {
                "bash_command": f"cf create-space {self.space_name}",
                "check": "OK",
            },
            {
                "bash_command": f"cf target -s {self.space_name}",
                "check": f"space:          {self.space_name}",
            },
            {
                "bash_command": f"cf create-service postgres tiny-unencrypted-11 {self.db_name}",
                "check": "OK",
            },
        ]  # List of bash commands and checks before it can move onto the next command

        for instruction in instructions:
            print(f""">>> {instruction["bash_command"]}""")
            self.bash_command(
                command=instruction["bash_command"],
                check=instruction["check"]
            )

        self.check_db_has_started()  # Checks if database has spun up correctly

        yes_pipe_process = subprocess.Popen(
            ["yes"],
            stdout=subprocess.PIPE
        )
        install_process = subprocess.Popen(
            "cf install-plugin conduit".split(" "),
            stdin=yes_pipe_process.stdout,
            stdout=subprocess.PIPE
        )
        yes_pipe_process.stdout.close()  # Allow ps_process to receive a SIGPIPE if grep_process exits.
        output = install_process.communicate()[0]
        if "successfully installed" not in output.decode("utf-8"):
            raise Exception(f"""yes | cf install-plugin conduit - {output.decode("utf-8")}""")

        os.system(f"cf conduit {self.db_name} -- psql < {self.backup_location}")
        os.system(f"cf conduit {self.db_name} -- psql < {self.backup_location}")

        self.create_manifest()  # Creates manifest before deloying Django app
        print(">>> pushing app to PaaS")
        subprocess.run(
            f"cf push -f {self.manifest_path}".split(),
            stderr=sys.stderr,
            stdout=sys.stdout,
            check=True
        )  # Deploys Django app
        print(f">>> website: {self.app_name}.london.cloudapps.digital")

    def clean_up(self):
        if os.path.exists(self.manifest_path):
            os.remove(self.manifest_path)  # Removes manifest

    def down(self):
        print(">>> breaking down environment in PaaS")
        attempts = 0
        while attempts < self.db_ping_attempts:
            process = subprocess.Popen(
                f"cf delete-space -f {self.space_name}".split(),
                stdout=subprocess.PIPE
            )  # delete-space triggers a deletion of all apps in space

            process = subprocess.Popen(
                "cf spaces".split(),
                stdout=subprocess.PIPE
            )  # Checks if space has been deleted
            output = process.communicate()[0]
            if self.space_name not in output.decode("utf-8"):
                print(f">>> {self.space_name} has been deleted")
                return
            attempts += 1
            time.sleep(self.db_ping_interval)

        raise Exception(f"""{self.space_name} did not break down correctly""")
