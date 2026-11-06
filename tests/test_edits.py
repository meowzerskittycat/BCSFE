"""Tests for editing logic (not just reading/writing)."""

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
