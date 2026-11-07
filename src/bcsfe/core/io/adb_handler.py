import shlex
from bcsfe import core
from bcsfe.core import io
from bcsfe.core import messages


class DeviceIDNotSet(Exception):
    pass


class AdbNotInstalled(Exception):
    def __init__(self, result: core.CommandResult):
        self.result = result


def parse_devices(output: str) -> list[str]:
    """The IDs of the ready devices in `adb devices` output."""
    devices: list[str] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def parse_packages(output: str) -> list[str]:
    """Package names from `find /data/data/ -name SAVE_DATA` output, which
    lists paths like /data/data/<package>/files/SAVE_DATA."""
    packages: list[str] = []
    for line in output.splitlines():
        # Some finds print "/data/data//<package>", so skip empty parts.
        parts = [part for part in line.strip().split("/") if part]
        if len(parts) >= 4 and parts[:2] == ["data", "data"]:
            if parts[2] not in packages:
                packages.append(parts[2])
    return packages


class AdbHandler(io.root_handler.RootHandler):
    def __init__(self, root: bool = True):
        self.root_avail = root
        adb_path = core.Path(core.core_data.config.get_str(core.ConfigKey.ADB_PATH))
        self.check_adb_installed(adb_path)
        self.adb_path = adb_path
        self.start_server()
        self.device_id = None
        self.package_name = None
        self.root_result = None

    @staticmethod
    def display_no_adb_error(e: AdbNotInstalled):
        messages.show(
            "adb_not_installed",
            path=core.core_data.config.get_str(core.ConfigKey.ADB_PATH),
            error=e,
        )

    def check_adb_installed(self, path: core.Path):
        result = path.run("version")
        if not result.success:
            raise AdbNotInstalled(result)

    def adb_root_success(self) -> bool:
        if self.root_result is None:
            return False
        result = self.root_result.result.strip()
        return (
            result != "adbd cannot run as root in production builds"
            and result != "not available in Waydroid"
        )

    def start_server(self) -> core.CommandResult:
        return self.adb_path.run("start-server")

    def kill_server(self) -> core.CommandResult:
        return self.adb_path.run("kill-server")

    def root(self) -> core.CommandResult:
        return self.adb_path.run("-s", self.get_device(), "root")

    def get_connected_devices(self) -> list[str]:
        """Devices ready to use. Unauthorized or offline ones are left out:
        nothing can be pulled from them until that's fixed on the device."""
        return parse_devices(self.adb_path.run("devices").result)

    def set_device(self, device_id: str):
        self.device_id = device_id
        if self.root_avail:
            self.root_result = self.root()

    def get_device(self) -> str:
        if self.device_id is None:
            raise DeviceIDNotSet("Device ID is not set")
        return self.device_id

    def get_device_name(self) -> str:
        return self.run_shell("getprop ro.product.model").result.strip()

    def run_shell(self, command: str) -> core.CommandResult:
        """Run `command` in the device's shell (a shell string, quote paths)."""
        return self.adb_path.run("-s", self.get_device(), "shell", command)

    def run_root_shell(self, command: str) -> core.CommandResult:
        return self.run_shell(f"su -c {shlex.quote(command)}")

    def adb_pull_file(
        self, device_path: core.Path, local_path: core.Path
    ) -> core.CommandResult:
        return self.adb_path.run(
            "-s",
            self.get_device(),
            "pull",
            device_path.to_str_forwards(),
            str(local_path),
        )

    def pull_file(
        self, device_path: core.Path, local_path: core.Path
    ) -> core.CommandResult:
        if not self.adb_root_success():
            src = shlex.quote(device_path.to_str_forwards())
            tmp = shlex.quote(f"/sdcard/{device_path.basename()}")
            result = self.run_root_shell(f"cp {src} {tmp} && chmod o+rw {tmp}")
            if result.exit_code != 0:
                return result
            device_path = core.Path("/sdcard/").add(device_path.basename())

        result = self.adb_pull_file(device_path, local_path)

        if not result.success:
            return result
        if not self.adb_root_success():
            # The save is already pulled; a leftover copy isn't a failure.
            self.run_shell(f"rm {shlex.quote(f'/sdcard/{device_path.basename()}')}")
        return result

    def adb_push_file(
        self, local_path: core.Path, device_path: core.Path
    ) -> core.CommandResult:
        return self.adb_path.run(
            "-s",
            self.get_device(),
            "push",
            str(local_path),
            device_path.to_str_forwards(),
        )

    def push_file(
        self, local_path: core.Path, device_path: core.Path
    ) -> core.CommandResult:
        orignal_device_path = device_path.copy_object()
        if not self.adb_root_success():
            device_path = core.Path("/sdcard/").add(device_path.basename())

        result = self.adb_push_file(local_path, device_path)
        if not result.success:
            return result
        if not self.adb_root_success():
            tmp = shlex.quote(f"/sdcard/{device_path.basename()}")
            dst = shlex.quote(orignal_device_path.to_str_forwards())
            result2 = self.run_root_shell(f"cp {tmp} {dst} && chmod o+rw {dst}")
            result3 = self.run_shell(f"rm {tmp}")
            if result2.exit_code != 0:
                return result2
            if result3.exit_code != 0:
                return result3

        return result

    def stat_file(self, device_path: core.Path) -> core.CommandResult:
        return self.run_shell(f"stat {shlex.quote(device_path.to_str_forwards())}")

    def does_file_exist(self, device_path: core.Path) -> bool:
        return self.stat_file(device_path).success

    def get_battlecats_packages(self) -> list[str]:
        cmd = "find /data/data/ -name SAVE_DATA -mindepth 3 -maxdepth 3"
        result = self.run_root_shell(cmd)
        if not result.success:
            return []
        return parse_packages(result.result)

    def save_battlecats_save(self, local_path: core.Path) -> core.CommandResult:
        result = self.pull_file(self.get_battlecats_save_path(), local_path)
        return result

    def load_battlecats_save(self, local_path: core.Path) -> core.CommandResult:
        return self.push_file(local_path, self.get_battlecats_save_path())

    def close_game(self) -> core.CommandResult:
        return self.run_shell(f"am force-stop {shlex.quote(self.get_package_name())}")

    def run_game(self) -> core.CommandResult:
        return self.run_shell(
            f"monkey --pct-syskeys 0 -p {shlex.quote(self.get_package_name())} 1"
        )
