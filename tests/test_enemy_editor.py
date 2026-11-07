"""Picking enemies for the enemy guide."""

from collections.abc import Iterator

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.edits import enemy_editor

from .conftest import real_fixtures


def answer(monkeypatch: pytest.MonkeyPatch, *answers: str) -> Iterator[str]:
    it = iter(answers)
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(it))
    return it


@pytest.fixture(autouse=True)
def no_names(monkeypatch: pytest.MonkeyPatch) -> None:
    # Names come from game data, which these tests don't need.
    monkeypatch.setattr(
        enemy_editor.EnemyEditor, "print_selected_enemies", lambda *_a: None
    )


def editor() -> enemy_editor.EnemyEditor:
    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    return enemy_editor.EnemyEditor(save)


def test_the_last_enemy_can_be_picked_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    e = editor()
    last = len(e.save_file.enemy_guide) - 1
    answer(monkeypatch, str(last + enemy_editor.WIKI_OFFSET))
    assert e.select_id() == [core.Enemy(last)]


def test_and_keeps_enemies_in_both_selections(monkeypatch: pytest.MonkeyPatch) -> None:
    e = editor()
    # Select ids 2-5 (indexes 0-3), then AND with ids 4-9 (indexes 2-7).
    answer(monkeypatch, "3", "4-9", "1")
    current = e.get_enemies_by_id([0, 1, 2, 3])
    assert e.select(current) == [core.Enemy(2), core.Enemy(3)]


def test_or_has_no_duplicates(monkeypatch: pytest.MonkeyPatch) -> None:
    e = editor()
    answer(monkeypatch, "3", "4-9", "2")
    current = e.get_enemies_by_id([0, 1, 2, 3])
    assert e.select(current) == [core.Enemy(i) for i in range(8)]
