"""Tests for editing logic (not just reading/writing)."""

import json

from bcsfe import core
from bcsfe.core.game.map.zero_legends import Chapter, ChaptersStars, Stage


def zero_legends(maps: int, stars: int, stages: int) -> core.ZeroLegendsChapters:
    return core.ZeroLegendsChapters(
        [
            ChaptersStars(
                0,
                [
                    Chapter(0, 0, 0, [Stage(0) for _ in range(stages)])
                    for _ in range(stars)
                ],
            )
            for _ in range(maps)
        ]
    )


def test_zero_legends_new_maps_have_independent_stages() -> None:
    zl = zero_legends(maps=1, stars=2, stages=3)
    zl.set_total_stages(1, 3)  # creates map 1
    zl.clear_stage(1, 0, 0)
    stars = zl.chapters[1].chapters
    assert [s.clear_times for s in stars[0].stages] == [1, 0, 0]
    assert [s.clear_times for s in stars[1].stages] == [0, 0, 0]


def test_zero_legends_clearing_unlocks() -> None:
    zl = zero_legends(maps=2, stars=2, stages=2)
    zl.set_total_stages(0, 2)
    zl.clear_stage(0, 0, 0)
    assert zl.chapters[0].chapters[0].unlock_state == 3
    assert zl.chapters[0].chapters[1].unlock_state == 0
    zl.clear_stage(0, 0, 1)  # last stage of the star
    assert zl.chapters[0].chapters[1].unlock_state == 1

    data = core.Data()
    zl.write(data)
    data.reset_pos()
    assert core.ZeroLegendsChapters.read(data) == zl


def run_chapter_menu(monkeypatch, answers: list[str]) -> tuple[list[str], list[str]]:
    """Drive the gauntlet/event/legend chapter menu with typed answers.

    Returns the edits that ran and the answers left unread."""
    from bcsfe.cli import color, edits

    left = list(answers)
    monkeypatch.setattr(color, "color_input", lambda *a, **k: left.pop(0))
    monkeypatch.setattr(color, "color_print_key", lambda *a, **k: None)
    calls: list[str] = []
    monkeypatch.setattr(
        edits.map, "edit_chapters2_clear_count", lambda *a, **k: calls.append("counts")
    )
    monkeypatch.setattr(
        edits.map,
        "edit_chapters2_progress",
        lambda *a, allow_unclear=False, **k: calls.append(
            "unclear" if allow_unclear else "clear"
        ),
    )
    edits.map.edit_chapters(None, core.Chapters([]), "A", 0)  # type: ignore[arg-type]
    return calls, left


def test_chapter_menu_finish_does_not_start_an_edit(monkeypatch) -> None:
    # "Finish" used to fall through to the first entry and start an edit.
    assert run_chapter_menu(monkeypatch, ["4"]) == ([], [])


def test_chapter_menu_returns_after_each_edit(monkeypatch) -> None:
    # Picking an edit used to run it and then leave the menu.
    calls, left = run_chapter_menu(monkeypatch, ["3", "2", "1", "4"])
    assert calls == ["counts", "unclear", "clear"]
    assert left == []


def stage_maps(maps: int, stars: int, stages: int):
    from bcsfe.core.game.map.stage_grid import MapStars

    return [MapStars.new(stars, stages) for _ in range(maps)]


def test_gauntlet_clearing_last_stage_unlocks_next_star_and_map() -> None:
    # The real stage count was never set, so "last stage" was never reached
    # and clearing a gauntlet never unlocked the next crown or map.
    g = core.GauntletChapters(stage_maps(2, 2, 3), [0, 0])
    for stage in range(3):
        g.clear_stage(0, 0, stage)
    assert g.chapters[0].chapters[1].chapter_unlock_state == 1
    assert g.chapters[1].chapters[0].chapter_unlock_state == 1


def test_legend_quest_tries_round_trip() -> None:
    lq = core.LegendQuestChapters(stage_maps(2, 2, 3), [1, 2], [10, 11, 12])
    lq.clear_stage(1, 1, 2, clear_amount=4)
    data = core.Data()
    lq.write(data)
    data.reset_pos()
    again = core.LegendQuestChapters.read(data)
    assert again == lq
    assert again.chapters[1].chapters[1].stages[2].tries == 4
    json_again = core.LegendQuestChapters.deserialize(
        json.loads(json.dumps(lq.serialize()))
    )
    assert json_again == lq


def test_event_dicts_have_int_keys_after_json_import() -> None:
    ev = core.EventChapters([])
    ev.chapter_completion_count = {14000: 3}
    loaded = core.EventChapters.deserialize(json.loads(json.dumps(ev.serialize())))
    loaded.chapter_completion_count[14000] += 1  # what the uncanny editor does
    assert loaded.chapter_completion_count == {14000: 4}
