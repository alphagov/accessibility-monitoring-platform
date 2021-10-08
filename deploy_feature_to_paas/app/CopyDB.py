import os
import subprocess


class CopyDB:
    def __init__(
        self,
        space_name: str,
        db_name: str,
        path: str,
    ):
        self.space_name = space_name
        self.db_name = db_name
        self.path = path

    def bash_command(self, command: str, check: str):
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE
        )
        output = process.communicate()[0]
        if check not in output.decode("utf-8"):
            raise Exception(f"""Error during {command} - {output.decode("utf-8")}""")
        return True

    def start(self):
        self.change_space()
        self.copy_db()

    def change_space(self):
        print(f">>> changing space to {self.space_name}")
        command = f"cf target -s {self.space_name}"
        check = f"space:          {self.space_name}"
        self.bash_command(
            command=command,
            check=check,
        )

    def copy_db(self):
        os.system(f"cf conduit {self.db_name} -- pg_dump -f {self.path}")
        return True

    def clean_up(self):
        if os.path.exists(self.path):
            os.remove(self.path)  # Removes manifest
