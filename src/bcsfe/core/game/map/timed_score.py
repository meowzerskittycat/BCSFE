"""Timed score stages: one score per stage, `sub_chapters[map][star][stage]`.
See `stage_grid.read_cube` for the layout."""

from bcsfe import core
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.io.schema import I32


class TimedScoreChapters:
    def __init__(self, sub_chapters: grid.Cube[int]):
        self.sub_chapters = sub_chapters

    @staticmethod
    def init(gv: core.GameVersion) -> TimedScoreChapters:
        return TimedScoreChapters(grid.new_cube(gv.game_version, 0))

    @staticmethod
    def read(stream: core.Data, gv: core.GameVersion) -> TimedScoreChapters:
        return TimedScoreChapters(grid.read_cube(stream, gv.game_version, I32))

    def write(self, stream: core.Data, gv: core.GameVersion):
        grid.write_cube(stream, gv.game_version, self.sub_chapters, I32)

    def serialize(self) -> grid.Cube[int]:
        return self.sub_chapters

    @staticmethod
    def deserialize(data: grid.Cube[int]) -> TimedScoreChapters:
        return TimedScoreChapters(
            [[[int(score) for score in star] for star in map] for map in data]
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TimedScoreChapters)
            and self.sub_chapters == other.sub_chapters
        )

    def __repr__(self) -> str:
        return f"TimedScoreChapters({self.sub_chapters})"
