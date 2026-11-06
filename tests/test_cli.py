"""Tests for the interactive menu and prompts, driven with typed answers."""

from collections.abc import Iterator

import pytest

from bcsfe import core
from bcsfe.cli import color, dialog_creator
from bcsfe.cli.feature_handler import FeatureHandler
from bcsfe.cli.save_management import SaveManagement

from .conftest import real_fixtures


def type_answers(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> list[str]:
    """Make prompts read `answers` in order; returns what's left unread."""
    left = list(answers)

    def fake_input(_: str) -> str:
        if not left:
            raise KeyboardInterrupt
        return left.pop(0)

    monkeypatch.setattr(color, "color_input", fake_input)
    return left


@pytest.fixture
def handler(monkeypatch: pytest.MonkeyPatch) -> Iterator[FeatureHandler]:
    monkeypatch.setattr(color, "color_print", lambda *a, **k: None)
    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    yield FeatureHandler(save)


def test_menu_has_no_go_back_at_the_top(handler: FeatureHandler, monkeypatch) -> None:
    shown: list[bool] = []
    monkeypatch.setattr(
        handler, "show", lambda title, entries, back: shown.append(back)
    )
    type_answers(monkeypatch, ["2", "0"])
    path, _ = handler.ask(())
    assert path == ("items",)
    path, _ = handler.ask(path)
    assert path == ()
    assert shown == [False, True]


def test_search_ranks_exact_names_first_and_runs_them(
    handler: FeatureHandler, monkeypatch
) -> None:
    found = handler.search_features("battle items")
    assert [p[-1] for p in found[:2]] == ["battle_items", "battle_items_endless"]

    type_answers(monkeypatch, ["Battle Items"])
    assert handler.ask(("gatya",)) == (("gatya",), ("items", "battle_items"))


def test_failed_feature_leaves_the_save_unchanged(
    handler: FeatureHandler, monkeypatch
) -> None:
    printed: list[str] = []
    monkeypatch.setattr(color, "color_print_key", lambda key, **k: printed.append(key))
    original = handler.save_file.catfood

    def broken(save_file: core.SaveFile):
        save_file.catfood = 12345
        raise ValueError("boom")

    def cancelled(save_file: core.SaveFile):
        save_file.catfood = 54321
        raise KeyboardInterrupt

    for feature in (broken, cancelled):
        monkeypatch.setattr(handler, "get_feature", lambda path, f=feature: f)
        handler.run(("items", "catfood"))
        assert handler.save_file.catfood == original
    assert printed == ["feature_failed", "feature_cancelled"]
    assert handler.undo_stack == []


def test_blank_answers_cancel_or_keep(monkeypatch) -> None:
    monkeypatch.setattr(color, "color_print", lambda *a, **k: None)
    type_answers(monkeypatch, [""])
    assert dialog_creator.edit_int_raw("x", 7, dialog_creator.MaxValue.i32()) == 7
    type_answers(monkeypatch, [""])
    assert dialog_creator.basic_pick_raw_index(["a", "b"], "pick") is None
    type_answers(monkeypatch, [""])
    assert dialog_creator.multi_select_indexes_raw(["a", "b", "c"], "pick") is None


def test_multi_select_rejects_bad_entries_without_keeping_them(monkeypatch) -> None:
    printed: list[dict[str, object]] = []
    monkeypatch.setattr(color, "color_print", lambda *a, **k: None)
    monkeypatch.setattr(color, "color_print_key", lambda key, **k: printed.append(k))
    type_answers(monkeypatch, ["1 9", "1 3"])
    assert dialog_creator.multi_select_indexes_raw(["a", "b", "c"], "pick") == [0, 2]
    assert printed == [{"min": 1, "max": 4}]


def test_closed_input_acts_like_ctrl_c(monkeypatch) -> None:
    def closed(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", closed)
    with pytest.raises(KeyboardInterrupt):
        color.color_input("?")


def test_no_color(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert color.colorize("<@e>error</>") == "error"
    monkeypatch.delenv("NO_COLOR")
    assert "\x1b[" in color.colorize("<@e>error</>")


@pytest.mark.parametrize(
    ("text", "version"),
    [
        ("12.2.1", 120201),
        ("15.7", 150700),
        ("5", None),
        ("1.2.3.4", None),
        ("0.1.0", None),
        ("15.100.0", None),
        ("a.b", None),
    ],
)
def test_game_version_input(text: str, version: int | None) -> None:
    gv = SaveManagement.parse_game_version(text)
    assert (gv.game_version if gv else None) == version


def test_undo_restores_previous_edits_in_order(
    handler: FeatureHandler, monkeypatch
) -> None:
    printed: list[str] = []
    monkeypatch.setattr(color, "color_print_key", lambda key, **k: printed.append(key))
    original = handler.save_file.catfood
    features = handler.get_features()

    def set_catfood(amount: int):
        def feature(save_file: core.SaveFile):
            save_file.catfood = amount

        return feature

    for feature in (set_catfood(111), set_catfood(222), set_catfood(222)):
        monkeypatch.setattr(handler, "get_feature", lambda path, f=feature: f)
        handler.run(("items", "catfood"))
    assert len(handler.undo_stack) == 2  # the last one changed nothing

    monkeypatch.setattr(handler, "get_feature", lambda path: features["undo_last_edit"])
    handler.run(("undo_last_edit",))
    assert handler.save_file.catfood == 111
    handler.run(("undo_last_edit",))
    assert handler.save_file.catfood == original
    handler.run(("undo_last_edit",))
    assert printed[-1] == "undo_nothing"


@pytest.mark.parametrize(
    ("latest", "installed", "expected"),
    [
        (("3.6.0", "b" * 40), "a" * 40, True),  # same version, newer commit
        (("3.6.0", "a" * 40), "a" * 40, False),  # already on the latest commit
        (("3.7.0", "a" * 40), None, True),  # newer version, not a git install
        (("3.6.0", "b" * 40), None, False),  # can't tell, so don't offer
        (("3.5.0", "b" * 40), "a" * 40, False),  # main is behind this install
    ],
)
def test_updater_follows_this_fork(
    monkeypatch, latest: tuple[str, str], installed: str | None, expected: bool
) -> None:
    from bcsfe.core.server import updater

    monkeypatch.setattr(updater.bcsfe, "__version__", "3.6.0")
    monkeypatch.setattr(
        updater.Updater, "installed_commit", staticmethod(lambda: installed)
    )
    up = updater.Updater()
    monkeypatch.setattr(up, "get_latest", lambda: latest)
    assert up.update_available() is expected


def test_updater_installs_from_github(monkeypatch) -> None:
    from bcsfe.core.server import updater

    ran: list[list[str]] = []

    class Done:
        exit_code = 0

    class FakeCommand:
        def __init__(self, cmd: list[str]):
            ran.append(cmd)

        def run(self):
            return Done()

    monkeypatch.setattr(updater.core, "Command", FakeCommand)
    up = updater.Updater()
    monkeypatch.setattr(up, "get_latest", lambda: ("3.6.0", "c" * 40))
    assert up.update()
    assert ran[0][-1] == "git+https://github.com/meowzerskittycat/BCSFE@" + "c" * 40


@pytest.mark.parametrize(
    ("code", "ok"),
    [("de", True), ("pt-BR", True), ("1 2", False), ("../x", False), ("ext-a", False)],
)
def test_locale_codes_must_be_one_word(code: str, ok: bool) -> None:
    assert core.Config.valid_locale_code(code) is ok


def test_new_locale_rejects_bad_codes_without_creating_anything(monkeypatch) -> None:
    before = core.LocalManager.get_all_locales()
    answers = iter(["1 2"])
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(answers))
    assert core.core_data.config.new_locale() is None
    assert core.LocalManager.get_all_locales() == before


def test_missing_locale_falls_back_to_english() -> None:
    assert core.LocalManager("does-not-exist").locale == "en"
