"""Main-style stage progress (also used by tower, challenge and uncanny)."""

from typing import Any

from bcsfe import core
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.game.map.stage_grid import MapStars, Stage, Star
from bcsfe.core.io.schema import I32

__all__ = ["Chapters", "ChaptersStars", "Chapter", "Stage"]

# Older names for the shared classes.
ChaptersStars = MapStars
Chapter = Star


def _skip_counts(data: core.Data, n: int):
    """Skip repeated counts; the first ones read are the ones used."""
    for _ in range(n):
        data.read_int()


class Chapters(grid.Maps):
    """Every value is an int.

    With `every_time` (the usual layout) the counts are repeated before each
    column; otherwise maps, stages and stars are given once at the start.
    """

    def __init__(self, chapters: list[MapStars]):
        self.chapters = chapters

    @staticmethod
    def init() -> Chapters:
        return Chapters([])

    @staticmethod
    def read(data: core.Data, read_every_time: bool = True) -> Chapters:
        if read_every_time:
            total_maps, total_stars = data.read_int(), data.read_int()
            total_stages = 0
        else:
            total_maps, total_stages, total_stars = (data.read_int() for _ in range(3))

        maps = grid.read_selected(data, total_maps, total_stars, I32)

        if read_every_time:
            _skip_counts(data, 2)
        grid.read_column(data, maps, "clear_progress", I32)

        if read_every_time:
            _skip_counts(data, 1)
            total_stages = data.read_int()
            _skip_counts(data, 1)
        grid.read_stages(data, maps, total_stages, I32)

        if read_every_time:
            _skip_counts(data, 2)
        grid.read_column(data, maps, "chapter_unlock_state", I32)

        return Chapters(maps)

    def get_lengths(self) -> tuple[int, int, int]:
        return grid.dims(self.chapters)

    def write(self, data: core.Data, write_every_time: bool = True):
        total_maps, total_stages, total_stars = self.get_lengths()
        if write_every_time:
            data.write_int(total_maps)
            data.write_int(total_stars)
        else:
            data.write_int(total_maps)
            data.write_int(total_stages)
            data.write_int(total_stars)
        grid.write_selected(data, self.chapters, I32)

        if write_every_time:
            data.write_int(total_maps)
            data.write_int(total_stars)
        grid.write_column(data, self.chapters, "clear_progress", I32)

        if write_every_time:
            data.write_int(total_maps)
            data.write_int(total_stages)
            data.write_int(total_stars)
        grid.write_stages(data, self.chapters, I32)

        if write_every_time:
            data.write_int(total_maps)
            data.write_int(total_stars)
        grid.write_column(data, self.chapters, "chapter_unlock_state", I32)

    def serialize(self) -> list[list[dict[str, Any]]]:
        return [map.to_json() for map in self.chapters]

    @staticmethod
    def deserialize(data: list[list[dict[str, Any]]]) -> Chapters:
        return Chapters([MapStars.from_json(map) for map in data])

    def __repr__(self) -> str:
        return f"Chapters({self.chapters})"
