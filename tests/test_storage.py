"""The storage editor: free space and leaving the menu."""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.edits import storage

from .conftest import real_fixtures


def answer(monkeypatch: pytest.MonkeyPatch, *answers: str) -> Iterator[str]:
    it = iter(answers)
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(it))
    return it


def save_with_free_slots(free: int) -> core.SaveFile:
    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    items = save.cats.storage_items
    for i, item in enumerate(items):
        item.item_type, item.item_id = (0, 0) if i < free else (1, 0)
    return save


def test_copies_of_a_skill_count_against_free_space(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    skills = SimpleNamespace(
        get_names_by_category=lambda _c: [
            (SimpleNamespace(id=0), "Skill A"),
            (SimpleNamespace(id=1), "Skill B"),
        ]
    )
    monkeypatch.setattr(core.core_data, "get_gatya_item_buy", lambda _s: skills)
    save = save_with_free_slots(2)
    answer(monkeypatch, "1", "5")  # Skill A, five copies, two free slots

    storage.add_special_skills(save)

    assert storage.get_storage_space(save.cats.storage_items) == 2


@pytest.mark.parametrize("key", ["", "q"])
def test_enter_or_quit_leaves_the_menu(
    monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    left = answer(monkeypatch, key)
    storage.edit_storage(save_with_free_slots(2))
    assert next(left, None) is None
