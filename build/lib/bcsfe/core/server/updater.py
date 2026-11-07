"""Updates the editor from this fork's GitHub repository.

`pip install bcsfe` would install upstream's editor, so updates come from the
repository's main branch instead. A git install records the commit it was
installed from (PEP 610's direct_url.json), which is compared with the latest
commit on main; other installs fall back to comparing version numbers.
"""

import json
import sys
from importlib import metadata
from typing import Any

import bcsfe
from bcsfe import __app_name__, core

REPO = "meowzerskittycat/BCSFE"
BRANCH = "main"
REPO_URL = f"https://github.com/{REPO}"


class Updater:
    def __init__(self):
        self._latest: tuple[str, str] | None = None

    @staticmethod
    def installed_commit() -> str | None:
        """The commit a git install was made from, if known."""
        try:
            text = metadata.distribution(__app_name__).read_text("direct_url.json")
        except metadata.PackageNotFoundError:
            return None
        if not text:
            return None
        try:
            commit = json.loads(text).get("vcs_info", {}).get("commit_id")
        except json.JSONDecodeError, AttributeError:
            return None
        return commit if isinstance(commit, str) and commit else None

    def get_local_version(self) -> str:
        return self.describe(bcsfe.__version__, self.installed_commit())

    @staticmethod
    def describe(version: str, commit: str | None) -> str:
        return f"{version} ({commit[:7]})" if commit else version

    @staticmethod
    def get_json(url: str) -> Any:
        response = core.RequestHandler(
            url, headers={"User-Agent": "BCSFE-Updater"}
        ).get()
        if response is None or response.status_code != 200:
            return None
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    @staticmethod
    def parse_version(source: str) -> str | None:
        for line in source.splitlines():
            if line.startswith("__version__"):
                return line.split("=", 1)[1].strip().strip("\"'")
        return None

    def get_latest(self) -> tuple[str, str] | None:
        """(version, commit) of the latest commit on main."""
        if self._latest is not None:
            return self._latest
        commit: dict[str, Any] | None = self.get_json(
            f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
        )
        sha = commit.get("sha") if isinstance(commit, dict) else None
        if not isinstance(sha, str):
            return None
        response = core.RequestHandler(
            f"https://raw.githubusercontent.com/{REPO}/{sha}/src/bcsfe/__init__.py",
            headers={"User-Agent": "BCSFE-Updater"},
        ).get()
        if response is None or response.status_code != 200:
            return None
        version = self.parse_version(response.text)
        if version is None:
            return None
        self._latest = (version, sha)
        return self._latest

    def get_latest_version(self) -> str | None:
        latest = self.get_latest()
        return self.describe(*latest) if latest else None

    def update_available(self) -> bool:
        latest = self.get_latest()
        if latest is None:
            return False
        version, sha = latest
        if self.version_check(version, bcsfe.__version__):
            return True
        installed = self.installed_commit()
        return (
            installed is not None
            and installed != sha
            and not self.version_check(bcsfe.__version__, version)
        )

    def update(self) -> bool:
        latest = self.get_latest()
        if latest is None:
            return False
        package = f"git+{REPO_URL}@{latest[1]}"
        pips = [
            [python, "-m", "pip"]
            for python in [sys.executable, "py", "python", "python3"]
            if python
        ]
        pips += [["pip"], ["pip3"]]
        for pip in pips:
            # Commits often share a version number, and pip skips installing
            # a version that's already installed, even with --upgrade. So
            # reinstall the editor itself, then install any new dependencies
            # without rebuilding the existing ones (slow on Termux).
            reinstall = [*pip, "install", "--force-reinstall", "--no-deps", package]
            if core.Command(reinstall).run().exit_code == 0:
                return core.Command([*pip, "install", package]).run().exit_code == 0
        return False

    @staticmethod
    def version_check(v1: str, v2: str) -> bool:
        """Whether version `v1` is newer than `v2`."""
        v1_p = v1.split(".")
        v2_p = v2.split(".")

        for p1, p2 in zip(v1_p, v2_p, strict=False):
            if not p1.isdigit() or not p2.isdigit():
                continue
            if int(p1) != int(p2):
                return int(p1) > int(p2)

        return len(v1_p) > len(v2_p)
