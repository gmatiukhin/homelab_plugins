import subprocess
from ansible.errors import AnsibleError
from ansible.config.manager import to_native


class TerraformCommand:
    def __init__(self, binary, cwd) -> None:
        self.binary = binary
        self.cwd = cwd

    def show(self) -> str:
        self.refresh()

        try:
            return subprocess.run(
                [self.binary, "show", "--json"],
                cwd=self.cwd,
                check=True,
                capture_output=True,
            ).stdout.decode("utf-8")
        except ChildProcessError as e:
            raise AnsibleError("Error executing `terraform show`: %s" % to_native(e))

    def refresh(self) -> None:
        try:
            subprocess.run(
                [self.binary, "refresh"],
                cwd=self.cwd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except ChildProcessError as e:
            raise AnsibleError("Error executing `terraform refresh`: %s" % to_native(e))
