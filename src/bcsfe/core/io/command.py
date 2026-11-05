from __future__ import annotations

import shlex
import subprocess
import threading
from collections.abc import Sequence


class CommandResult:
    def __init__(self, result: str, exit_code: int):
        self.result = result
        self.exit_code = exit_code

    def __str__(self) -> str:
        return self.result

    def __repr__(self) -> str:
        return f"Result({self.result!r}, {self.exit_code!r})"

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    @staticmethod
    def create_success(result: str = "") -> CommandResult:
        return CommandResult(result, 0)

    @staticmethod
    def create_failure(result: str = "") -> CommandResult:
        return CommandResult(result, 1)


class Command:
    """Runs a program without going through a shell.

    `args` is the program followed by its arguments. Each argument is passed
    to the program exactly as given, so paths containing spaces or quotes,
    and URLs supplied by users, can't be split up or run as extra commands.
    """

    def __init__(self, args: Sequence[str], display_output: bool = True):
        if isinstance(args, str):
            raise TypeError("Command takes a list of arguments, not a shell string")
        self.args = list(args)
        self.display_output = display_output

    @property
    def command(self) -> str:
        return shlex.join(self.args)

    def run(self, inputData: str = "\n") -> CommandResult:
        try:
            self.process = subprocess.Popen(
                self.args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
        except OSError as e:
            # program not found / not executable: mirror a shell's exit code
            return CommandResult(str(e), 127)
        output, _ = self.process.communicate(inputData)
        return_code = self.process.wait()
        return CommandResult(output, return_code)

    def run_in_thread(self, inputData: str = "\n") -> None:
        self.thread = threading.Thread(target=self.run, args=(inputData,))
        self.thread.start()
