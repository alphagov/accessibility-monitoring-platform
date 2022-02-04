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

    def start(self):
        """Starts the master command"""
        self.change_space()
        self.install_conduit()
        self.copy_db()

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

    def change_space(self):
        """Changes space in cloud foundry"""
        print(f">>> changing space to {self.space_name}")
        command: str = f"cf target -s {self.space_name}"
        check: str = f"space:          {self.space_name}"
        self.bash_command(
            command=command,
            check=check,
        )

    def copy_db(self):
        """Copies the database to a local dir"""
        os.system(f"cf conduit {self.db_name} -- pg_dump -f {self.path}")
        return True

    def clean_up(self):
        """Cleans up locally stored files"""
        if os.path.exists(self.path):
            os.remove(self.path)  # Removes manifest
