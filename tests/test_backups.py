"""Backups made when a save is loaded can be listed, pruned and restored."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.save_management import SaveManagement

from .conftest import real_fixtures

DATES = ["2026-01-02_03-04-05", "2026-03-01_00-00-00", "2025-12-31_23-59-59"]


@pytest.fixture
def saves(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[core.Path]:
    folder = core.Path(str(tmp_path))
    monkeypatch.setattr(core.SaveFile, "get_saves_path", staticmethod(lambda: folder))
    yield folder


def make_backups(saves: core.Path) -> None:
    data = core.Data(real_fixtures()[0].read_bytes())
    folder = saves.add("backups").add("en").add("inquiry").generate_dirs()
    for date in DATES:
        folder.add(date).write(data)
    folder.add("not a backup").write(data)


def answer(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: text)


def test_backups_are_listed_newest_first(saves: core.Path) -> None:
    make_backups(saves)
    backups = core.SaveFile.get_backups()
    assert [path.basename() for path, *_ in backups] == sorted(DATES, reverse=True)
    assert {(cc, inquiry) for _, _, cc, inquiry in backups} == {("en", "inquiry")}


def test_old_backups_are_pruned(saves: core.Path) -> None:
    make_backups(saves)
    config = core.core_data.config
    before = config.get_int(core.ConfigKey.MAX_BACKUPS)
    config.set(core.ConfigKey.MAX_BACKUPS, 1)
    try:
        core.SaveFile.check_backups()
    finally:
        config.set(core.ConfigKey.MAX_BACKUPS, before)
    assert [p.basename() for p, *_ in core.SaveFile.get_backups()] == [DATES[1]]


@pytest.mark.parametrize("limit", [-1, -2])
def test_a_negative_limit_keeps_every_backup(saves: core.Path, limit: int) -> None:
    make_backups(saves)
    config = core.core_data.config
    before = config.get_int(core.ConfigKey.MAX_BACKUPS)
    config.set(core.ConfigKey.MAX_BACKUPS, limit)
    try:
        core.SaveFile.check_backups()
    finally:
        config.set(core.ConfigKey.MAX_BACKUPS, before)
    assert len(core.SaveFile.get_backups()) == len(DATES)


def test_a_restored_backup_is_loaded_without_a_save_path(
    saves: core.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_backups(saves)
    answer(monkeypatch, "1")  # the newest
    loaded = SaveManagement.restore_backup()
    assert loaded is not None
    save, path = loaded
    assert path.basename() == DATES[1]
    # Saving asks where to put it rather than overwriting the backup.
    assert save.save_path is None
    # Restoring doesn't make another backup.
    assert len(core.SaveFile.get_backups()) == len(DATES)


def test_restoring_with_no_backups_says_so(saves: core.Path) -> None:
    assert SaveManagement.restore_backup() is None
