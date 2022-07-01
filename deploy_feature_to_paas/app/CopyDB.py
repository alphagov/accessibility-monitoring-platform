"""CopyDB - Copies DB to local path"""
import os
import subprocess


class CopyDB:
    """CopyDB - Copies DB to local path"""

    def __init__(
        self,
        space_name: str,
        db_name: str,
        path: str,
    ):
        self.space_name: str = space_name
        self.db_name: str = db_name
        self.path: str = path

    def start(self):
        """Starts the master command"""
        self.change_space()
        self.install_conduit()
        self.copy_db()

    def install_conduit(self) -> bool:
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

        # Allow ps_process to receive a SIGPIPE if grep_process exits.
        yes_pipe_process.stdout.close()  # type: ignore
        output: bytes = install_process.communicate()[0]
        if "successfully installed" not in output.decode("utf-8"):
            raise Exception(
                f"""yes | cf install-plugin conduit - {output.decode("utf-8")}"""
            )
        return True

    def change_space(self) -> bool:
        """Changes space in cloud foundry"""
        print(f">>> changing space to {self.space_name}")
        command: str = f"cf target -s {self.space_name}"
        check: str = f"space:          {self.space_name}"

        process: subprocess.Popen = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
        )

        output: bytes = process.communicate()[0]

        if check not in output.decode("utf-8"):
            raise Exception(f"""Error during {command} - {output.decode("utf-8")}""")
        return True

    def copy_db(self) -> bool:
        """Copies the database to a local dir"""
        os.system(f"cf conduit {self.db_name} -- pg_dump -f {self.path}")
        return True

    def clean_up(self) -> bool:
        """Cleans up locally stored files"""
        if os.path.exists(self.path):
            os.remove(self.path)  # Removes manifest
        return True
