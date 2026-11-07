"""Leaving the editor offers to save changes, and copes with a moved save."""

import pytest

from bcsfe import core
from bcsfe.cli import color, main, save_management

from .conftest import real_fixtures


def leave(monkeypatch: pytest.MonkeyPatch, save: core.SaveFile, answer: str) -> bool:
    """Exit with `answer` to "save before exiting?"; whether it saved."""
    saved: list[core.SaveFile] = []
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: answer)
    monkeypatch.setattr(
        save_management.SaveManagement, "save_save", lambda s: saved.append(s)
    )
    with pytest.raises(SystemExit):
        main.Main.exit_editor(save, check_temp=False)
    return bool(saved)


def changed_save() -> core.SaveFile:
    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    save.catfood += 1
    return save


@pytest.mark.parametrize("answer", ["y", "Y", "yes"])
def test_yes_saves(monkeypatch: pytest.MonkeyPatch, answer: str) -> None:
    assert leave(monkeypatch, changed_save(), answer)


def test_no_doesnt_save(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not leave(monkeypatch, changed_save(), "n")


def test_a_moved_save_still_offers_to_save(monkeypatch: pytest.MonkeyPatch) -> None:
    save = changed_save()
    save.save_path = core.Path("/nonexistent/folder/SAVE_DATA")
    assert leave(monkeypatch, save, "y")
