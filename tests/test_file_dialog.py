"""The typed file dialog (used when the system dialog is off)."""

import sys
import types
from collections.abc import Iterator

import pytest

from bcsfe import core
from bcsfe.cli import color, file_dialog


@pytest.fixture
def typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core.core_data.config, "get_bool", lambda _k: False)


def answer(monkeypatch: pytest.MonkeyPatch, *answers: str) -> Iterator[str]:
    it = iter(answers)
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(it))
    return it


@pytest.mark.usefixtures("typed")
def test_no_window_is_opened_when_the_dialog_is_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    windows: list[object] = []
    fake = types.ModuleType("tkinter")
    fake.Tk = lambda: windows.append(object())  # type: ignore[attr-defined]
    fake.TclError = Exception  # type: ignore[attr-defined]
    fake.filedialog = types.ModuleType("tkinter.filedialog")  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tkinter", fake)
    monkeypatch.setitem(sys.modules, "tkinter.filedialog", fake.filedialog)  # type: ignore[attr-defined]

    dialog = file_dialog.FileDialog()

    assert windows == []
    assert not dialog.use_tk()


@pytest.mark.usefixtures("typed")
def test_quit_cancels_saving(monkeypatch: pytest.MonkeyPatch) -> None:
    answer(monkeypatch, "q")
    assert (
        file_dialog.FileDialog().save_file("save_save_dialog", "/tmp", "SAVE_DATA")
        is None
    )


@pytest.mark.usefixtures("typed")
def test_blank_saves_to_the_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: core.Path
) -> None:
    answer(monkeypatch, "")
    path = file_dialog.FileDialog().save_file(
        "save_save_dialog", str(tmp_path), "SAVE_DATA"
    )
    assert path == core.Path(str(tmp_path)).add("SAVE_DATA").to_str()


@pytest.mark.usefixtures("typed")
def test_quotes_around_a_dragged_path_are_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer(monkeypatch, '"C:\\saves\\SAVE_DATA" ')
    path = file_dialog.FileDialog().save_file("save_save_dialog", "/tmp", "SAVE_DATA")
    assert path == "C:\\saves\\SAVE_DATA"
