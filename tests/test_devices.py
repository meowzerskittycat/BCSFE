"""Pulling and pushing saves over adb and waydroid, with the programs faked.

No device, adb or waydroid is needed: core.Command.run is replaced by a fake
that records each program call and answers from a script.
"""

from collections.abc import Callable

import pytest

from bcsfe import core
from bcsfe.core.io import adb_handler

Responder = Callable[[list[str], str], core.CommandResult | None]
SAVE = "/data/data/jp.co.ponos.battlecatsen/files/SAVE_DATA"


class FakePrograms:
    def __init__(self, responder: Responder) -> None:
        self.responder = responder
        self.calls: list[list[str]] = []

    def run(self, command: core.Command, input_data: str = "\n") -> core.CommandResult:
        self.calls.append(command.args)
        result = self.responder(command.args, input_data)
        return result if result is not None else core.CommandResult.create_success()

    def shell_commands(self) -> list[str]:
        """What was run in the device's shell, in order."""
        return [args[-1] for args in self.calls if "shell" in args]


def fake(monkeypatch: pytest.MonkeyPatch, responder: Responder) -> FakePrograms:
    programs = FakePrograms(responder)

    def run(command: core.Command, input_data: str = "\n") -> core.CommandResult:
        return programs.run(command, input_data)

    monkeypatch.setattr(core.Command, "run", run)
    return programs


def ok(_args: list[str], _input: str) -> None:
    return None


def adb(monkeypatch: pytest.MonkeyPatch, responder: Responder = ok):
    programs = fake(monkeypatch, responder)
    handler = core.AdbHandler(root=False)
    handler.set_device("R58M123")
    handler.set_package_name("jp.co.ponos.battlecatsen")
    return handler, programs


@pytest.mark.parametrize(
    ("output", "devices"),
    [
        ("List of devices attached\nemulator-5554\tdevice\n\n", ["emulator-5554"]),
        # No blank line at the end: the last device used to be dropped.
        ("List of devices attached\nA\tdevice\nB\tdevice\n", ["A", "B"]),
        ("List of devices attached\r\nA\tdevice\r\n", ["A"]),
        (
            "* daemon not running; starting now at tcp:5037\n"
            "* daemon started successfully\n"
            "List of devices attached\nA\tunauthorized\nB\toffline\nC\tdevice\n",
            ["C"],
        ),
        ("List of devices attached\n\n", []),
        ("", []),
    ],
)
def test_devices_are_parsed(output: str, devices: list[str]) -> None:
    assert adb_handler.parse_devices(output) == devices


@pytest.mark.parametrize(
    ("output", "packages"),
    [
        (f"{SAVE}\n", ["jp.co.ponos.battlecatsen"]),
        (
            "/data/data//jp.co.ponos.battlecatskr/files/SAVE_DATA\r\n",
            ["jp.co.ponos.battlecatskr"],
        ),
        (
            f"{SAVE}\n{SAVE}\n/data/data/jp.co.ponos.battlecats/files/SAVE_DATA\n",
            ["jp.co.ponos.battlecatsen", "jp.co.ponos.battlecats"],
        ),
        ("find: /data/data/x: Permission denied\n\n", []),
        ("", []),
    ],
)
def test_packages_are_parsed(output: str, packages: list[str]) -> None:
    assert adb_handler.parse_packages(output) == packages


def test_pulling_without_adb_root_copies_through_the_sdcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, programs = adb(monkeypatch)
    local = core.Path("local/SAVE_DATA")
    result = handler.pull_file(core.Path(SAVE), local)
    assert result.success
    shell = programs.shell_commands()
    assert shell[0].startswith("su -c ") and "/sdcard/SAVE_DATA" in shell[0]
    assert [
        "adb",
        "-s",
        "R58M123",
        "pull",
        "/sdcard/SAVE_DATA",
        "local/SAVE_DATA",
    ] in programs.calls
    assert shell[-1] == "rm /sdcard/SAVE_DATA"


def test_a_failed_cleanup_after_pulling_is_not_a_failed_pull(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def responder(args: list[str], _input: str) -> core.CommandResult | None:
        if args[-1].startswith("rm "):
            return core.CommandResult.create_failure("rm: Read-only file system")
        return None

    handler, _ = adb(monkeypatch, responder)
    assert handler.pull_file(core.Path(SAVE), core.Path("local")).success


def test_a_failed_copy_stops_the_pull(monkeypatch: pytest.MonkeyPatch) -> None:
    def responder(args: list[str], _input: str) -> core.CommandResult | None:
        if args[-1].startswith("su -c"):
            return core.CommandResult.create_failure("su: not found")
        return None

    handler, programs = adb(monkeypatch, responder)
    result = handler.pull_file(core.Path(SAVE), core.Path("local"))
    assert not result.success
    assert result.result == "su: not found"
    assert not any("pull" in args for args in programs.calls)


def test_pushing_without_adb_root_copies_through_the_sdcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, programs = adb(monkeypatch)
    assert handler.push_file(core.Path("local/SAVE_DATA"), core.Path(SAVE)).success
    assert [
        "adb",
        "-s",
        "R58M123",
        "push",
        "local/SAVE_DATA",
        "/sdcard/SAVE_DATA",
    ] in programs.calls
    shell = programs.shell_commands()
    assert shell[0].startswith("su -c ") and SAVE in shell[0]
    assert shell[-1] == "rm /sdcard/SAVE_DATA"


def test_no_adb_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    fake(monkeypatch, lambda args, _i: core.CommandResult("not found", 127))
    with pytest.raises(adb_handler.AdbNotInstalled):
        core.AdbHandler()


def waydroid_status(args: list[str], _input: str) -> core.CommandResult | None:
    if args == ["waydroid", "status"]:
        return core.CommandResult.create_success(
            "Session:\tRUNNING\nContainer:\tRUNNING\nIP address:\t192.168.240.112\n"
        )
    return None


def test_a_usb_device_is_not_waydroid(monkeypatch: pytest.MonkeyPatch) -> None:
    # USB devices have no ":port"; this used to raise ValueError.
    fake(monkeypatch, waydroid_status)
    assert not core.WayDroidHandler.is_waydroid("R58M123")


def test_waydroid_is_recognised_by_its_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    fake(monkeypatch, waydroid_status)
    assert core.WayDroidHandler.is_waydroid("192.168.240.112:5555")
    assert not core.WayDroidHandler.is_waydroid("192.168.1.5:5555")


def test_waydroid_pull_survives_a_failed_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def responder(args: list[str], _input: str) -> core.CommandResult | None:
        if args[-1].startswith("rm "):
            return core.CommandResult.create_failure("rm: denied")
        return None

    fake(monkeypatch, responder)
    handler = core.WayDroidHandler()
    handler.adb_handler.set_device("192.168.240.112:5555")
    handler.set_package_name("jp.co.ponos.battlecatsen")
    assert handler.pull_file(core.Path(SAVE), core.Path("local")).success


def test_loading_locally_reports_a_failed_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = core.RootHandler()
    failure = core.CommandResult.create_failure("denied")
    monkeypatch.setattr(handler, "load_battlecats_save", lambda _p: failure)
    monkeypatch.setattr(handler, "rerun_game", core.CommandResult.create_success)
    assert handler.load_locally(core.Path("x")) is failure


def test_a_broken_waydroid_falls_back_to_adb(monkeypatch: pytest.MonkeyPatch) -> None:
    from bcsfe.cli import save_management

    def responder(args: list[str], input_data: str) -> core.CommandResult | None:
        if args == ["waydroid", "-V"]:
            return core.CommandResult("waydroid: command failed", 1)
        return waydroid_status(args, input_data)

    fake(monkeypatch, responder)
    handler = core.AdbHandler(root=False)
    handler.set_device("192.168.240.112:5555")
    assert save_management.waydroid_if_needed(handler) is handler


def test_a_working_waydroid_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    from bcsfe.cli import save_management

    fake(monkeypatch, waydroid_status)
    handler = core.AdbHandler(root=False)
    handler.set_device("192.168.240.112:5555")
    waydroid = save_management.waydroid_if_needed(handler)
    assert isinstance(waydroid, core.WayDroidHandler)
    assert waydroid.adb_handler.get_device() == "192.168.240.112:5555"
