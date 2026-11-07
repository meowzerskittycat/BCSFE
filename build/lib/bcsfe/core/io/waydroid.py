import shlex

from bcsfe import core
from bcsfe.core import messages
from bcsfe.core import io
from bcsfe.core.io.command import CommandResult


class WayDroidNotInstalledError(Exception):
    def __init__(self, result: CommandResult):
        self.result = result


class WayDroidHandler(io.root_handler.RootHandler):
    def __init__(self):
        self.check_waydroid_installed()

        self.adb_handler = io.adb_handler.AdbHandler(root=False)

        self.package_name = None

    @staticmethod
    def get_waydroid_ip() -> str | None:
        res = io.command.Command(["waydroid", "status"]).run()
        if not res.success:
            return None

        ip_address = None
        for line in res.result.splitlines():
            key, _, value = line.partition(":")
            if key.strip() == "IP address":
                ip_address = value
                break

        return ip_address

    @staticmethod
    def is_waydroid(device: str) -> bool:
        waydroid_ip = WayDroidHandler.get_waydroid_ip()
        if waydroid_ip is None:
            return False

        # USB devices are named by serial number, with no ":port".
        ip, _, _ = device.partition(":")
        return ip == waydroid_ip.strip()

    def set_package_name(self, package_name: str):
        self.package_name = package_name
        self.adb_handler.set_package_name(self.package_name)

    @staticmethod
    def display_waydroid_not_installed(e: WayDroidNotInstalledError):
        messages.show("waydroid_not_installed", error=e)
        return

    @staticmethod
    def check_waydroid_installed():
        result = io.command.Command(["waydroid", "-V"]).run()
        if not result.success:
            raise WayDroidNotInstalledError(result)

    def run_shell_cmd(self, command: str) -> core.CommandResult:
        cmd = ["waydroid", "shell"]
        use_pkexec = core.core_data.config.get_bool(core.ConfigKey.USE_PKEXEC_WAYDROID)
        if use_pkexec:
            cmd = ["pkexec", *cmd]
        return io.command.Command(cmd).run(command)

    def pull_file(
        self, device_path: core.Path, local_path: core.Path
    ) -> core.CommandResult:
        # copy file to sdcard

        src = shlex.quote(device_path.to_str_forwards())
        tmp = shlex.quote(f"/sdcard/{device_path.basename()}")
        result = self.run_shell_cmd(f"cp {src} {tmp} && chmod o+rw {tmp}")

        if not result.success:
            return result

        device_path = core.Path("/sdcard/").add(device_path.basename())

        # adb pull

        result = self.adb_handler.adb_pull_file(device_path, local_path)
        if not result.success:
            return result

        # The save is already pulled; a leftover copy isn't a failure.
        self.adb_handler.run_shell(
            f"rm {shlex.quote(f'/sdcard/{device_path.basename()}')}"
        )
        return result

    def push_file(
        self, local_path: core.Path, device_path: core.Path
    ) -> core.CommandResult:
        original_device_path = device_path.copy_object()

        device_path = core.Path("/sdcard/").add(device_path.basename())

        # push to /sdcard with adb

        import time

        time.sleep(0.25)
        result = self.adb_handler.adb_push_file(local_path, device_path)

        if not result.success:
            return result

        tmp = shlex.quote(f"/sdcard/{device_path.basename()}")
        dst = shlex.quote(original_device_path.to_str_forwards())
        result = self.run_shell_cmd(f"cp {tmp} {dst} && chmod o+rw {dst}")

        if not result.success:
            return result

        # remove temp file
        #
        return self.adb_handler.run_shell(f"rm {tmp}")

    def get_battlecats_packages(self) -> list[str]:
        cmd = "find /data/data/ -name SAVE_DATA -mindepth 3 -maxdepth 3"
        result = self.run_shell_cmd(cmd)

        if not result.success:
            return []

        return io.adb_handler.parse_packages(result.result)

    def save_battlecats_save(self, local_path: core.Path) -> core.CommandResult:
        return self.pull_file(self.get_battlecats_save_path(), local_path)

    def load_battlecats_save(self, local_path: core.Path) -> core.CommandResult:
        return self.push_file(local_path, self.get_battlecats_save_path())

    def run_game(self) -> core.CommandResult:
        return self.adb_handler.run_game()

    def close_game(self) -> core.CommandResult:
        return self.adb_handler.close_game()
