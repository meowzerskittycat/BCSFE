import os
import shutil
import tempfile
from importlib import resources
from pathlib import Path

import pytest

from bcsfe import __app_name__, copy_to_data_dir, core

TESTS_DIR = Path(__file__).parent
SYNTHETIC_DIR = TESTS_DIR / "fixtures" / "synthetic"
# Saves from real accounts with the account details (inquiry code, password
# refresh token, transfer codes) replaced by placeholders.
REAL_FIXTURE_DIR = TESTS_DIR / "fixtures" / "real"
# Raw saves are never committed (they contain account credentials). Drop
# copies of your own saves in here to test against them locally, or run
# tests/tools/sanitize_save.py on one to turn it into a committed fixture.
REAL_SAVES_DIR = TESTS_DIR / "saves"
# Game data for the menu tests, downloaded by tests/tools/get_game_data.py
# (CI does this). Never committed.
GAME_DATA_DIR = TESTS_DIR / "game_data"
GAME_DATA_COPY = Path(tempfile.mkdtemp(prefix="bcsfe-game-data-")) / "game_data"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--all-answers",
        action="store_true",
        help="run every menu feature with each set of typed answers, not just one",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Point the editor at a throwaway data dir so tests never touch user files.

    This runs before collection, so tests can be parametrized over things
    that need the editor's data (like the feature menu).
    """
    data_dir = Path(tempfile.mkdtemp(prefix="bcsfe-data-"))
    config.add_cleanup(lambda: shutil.rmtree(data_dir, ignore_errors=True))
    config.add_cleanup(lambda: shutil.rmtree(GAME_DATA_COPY.parent, ignore_errors=True))
    core.set_data_dir_path(core.Path(str(data_dir)))
    # The config normally lives in the user's home; keep tests out of it.
    os.environ["XDG_CONFIG_HOME"] = str(data_dir / "config")
    core.set_config_path(core.Path(str(data_dir / "config.yaml")))
    core.set_log_path(core.Path(str(data_dir / "bcsfe.log")))
    files = resources.files(__app_name__).joinpath("files")
    copy_to_data_dir(files, files)
    core.core_data.init_data()


def synthetic_saves() -> list[Path]:
    return sorted(SYNTHETIC_DIR.glob("*.sav"))


def real_fixtures() -> list[Path]:
    return sorted(REAL_FIXTURE_DIR.glob("*.sav"))


def real_saves() -> list[Path]:
    if not REAL_SAVES_DIR.exists():
        return []
    return sorted(
        p for p in REAL_SAVES_DIR.rglob("*") if p.is_file() and p.name != ".gitkeep"
    )


def has_game_data() -> bool:
    return any(GAME_DATA_DIR.glob("*/*/downloaded"))


def use_game_data(enabled: bool, empty: Path) -> None:
    """Point the editor at a working copy of the test game data, or at an
    empty folder, and drop anything it loaded from the other.

    It's a copy because menus can change it: the game data manager deletes
    versions. A copy that lost anything is made again."""
    path = empty
    if enabled:
        path = GAME_DATA_COPY
        if not all(
            (path / marker.relative_to(GAME_DATA_DIR)).exists()
            for marker in GAME_DATA_DIR.glob("*/*/downloaded")
        ):
            shutil.rmtree(path, ignore_errors=True)
            shutil.copytree(GAME_DATA_DIR, path)
    core.set_game_data_path(core.Path(str(path)))
    core.core_data.init_data()
