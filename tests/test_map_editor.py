"""The shared map editor: picking maps and clearing stages."""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.edits import map as map_editor

from .conftest import real_fixtures

NO_CROWN_LIMIT = SimpleNamespace(get_map=lambda _id: None)


def answer(monkeypatch: pytest.MonkeyPatch, *answers: str) -> Iterator[str]:
    it = iter(answers)
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(it))
    return it


def load() -> core.SaveFile:
    return core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))


def clear_times(chapters: core.GauntletChapters, map_id: int, star: int) -> list[int]:
    return [s.clear_times for s in chapters.chapters[map_id].chapters[star].stages]


def test_searching_by_name_picks_that_map(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ids with gaps, as the clear-count menu uses (map * 10 + crown).
    names: dict[int, str | None] = {0: "Alpha", 10: "Beta", 21: "Gamma"}
    answer(monkeypatch, "gamma", "3")  # search, then finish selecting
    assert map_editor.select_map_names(names) == [21]


def test_a_blank_map_choice_cancels(monkeypatch: pytest.MonkeyPatch) -> None:
    left = answer(monkeypatch, "")
    assert map_editor.select_map_names({0: "Alpha", 1: "Beta"}) is None
    assert next(left, None) is None


def test_same_clear_count_for_all_maps(monkeypatch: pytest.MonkeyPatch) -> None:
    save = load()
    chapters = save.gauntlets
    monkeypatch.setattr(
        core, "MapNames", lambda *_a, **_k: SimpleNamespace(map_names={})
    )
    monkeypatch.setattr(core.MapOption, "from_save", lambda _s: NO_CROWN_LIMIT)
    monkeypatch.setattr(
        map_editor, "select_maps_stars", lambda *_a, **_k: [(0, 0), (1, 0)]
    )
    left = answer(monkeypatch, "1", "5")  # same count for all, then 5 clears

    map_editor.edit_chapters2_clear_count(save, chapters, "A", 24000)

    assert next(left, None) is None
    assert set(clear_times(chapters, 0, 0)) == {5}
    assert set(clear_times(chapters, 1, 0)) == {5}


def clear_up_to(
    monkeypatch: pytest.MonkeyPatch,
    save: core.SaveFile,
    stage_names: list[str],
    *answers: str,
) -> None:
    names = SimpleNamespace(stage_names={0: stage_names})
    for star in range(4):
        for stage in range(30):
            save.gauntlets.clear_stage(0, star, stage, 1)
    answer(monkeypatch, *answers)
    map_editor.clear_specific_stage_unclear(
        0,
        names,
        NO_CROWN_LIMIT,
        24000,
        save.gauntlets,
        None,
        allow_unclear=True,  # type: ignore[arg-type]
    )


def test_clearing_to_the_first_stage_unclears_the_rest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save = load()
    clear_up_to(
        monkeypatch, save, ["One", "Two", "Three"], "1", "1"
    )  # first stage, one crown
    g = save.gauntlets
    assert clear_times(g, 0, 0)[:3] == [1, 0, 0]
    assert set(clear_times(g, 0, 1)) == {0}


def test_clearing_with_no_crowns_unclears_the_whole_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save = load()
    clear_up_to(monkeypatch, save, ["One", "Two", "Three"], "2", "0")
    g = save.gauntlets
    for star in range(4):
        assert set(clear_times(g, 0, star)) == {0}


def test_a_stage_after_a_blank_name_keeps_its_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save = load()
    clear_up_to(
        monkeypatch, save, ["One", "", "Three", "Four"], "2", "1"
    )  # "Three" is stage 2
    assert clear_times(save.gauntlets, 0, 0)[:4] == [1, 1, 1, 0]
