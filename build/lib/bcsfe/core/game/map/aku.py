"""Aku realm stages: only the selected stage and clear counts are stored,
and each star's stages are stored together (not interleaved)."""

from typing import Any

from bcsfe import core
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.game.map.stage_grid import MapStars, Stage, Star
from bcsfe.core.io.schema import I8, I16

__all__ = ["AkuChapters", "ChaptersStars", "Chapter", "Stage"]

ChaptersStars = MapStars
Chapter = Star


def _star_to_json(star: Star) -> dict[str, Any]:
    return {
        "current_stage": star.selected_stage,
        "stages": [stage.clear_times for stage in star.stages],
    }


def _star_from_json(data: dict[str, Any]) -> Star:
    star = Star(data.get("current_stage", 0))
    star.stages = [Stage(clears) for clears in data.get("stages", [])]
    return star


class AkuChapters(grid.Maps):
    def __init__(self, chapters: list[MapStars]):
        self.chapters = chapters

    @staticmethod
    def init() -> AkuChapters:
        return AkuChapters([])

    @staticmethod
    def read(data: core.Data) -> AkuChapters:
        total_maps = data.read_short()
        total_stages = data.read_byte()
        total_stars = data.read_byte()
        maps = grid.read_selected(data, total_maps, total_stars, I8)
        grid.read_stages(data, maps, total_stages, I16, interleaved=False)
        return AkuChapters(maps)

    def write(self, data: core.Data):
        total_maps, total_stages, total_stars = grid.dims(self.chapters)
        data.write_short(total_maps)
        data.write_byte(total_stages)
        data.write_byte(total_stars)
        grid.write_selected(data, self.chapters, I8)
        grid.write_stages(data, self.chapters, I16, interleaved=False)

    def serialize(self) -> list[list[dict[str, Any]]]:
        return [[_star_to_json(star) for star in map.chapters] for map in self.chapters]

    @staticmethod
    def deserialize(data: list[list[dict[str, Any]]]) -> AkuChapters:
        return AkuChapters(
            [MapStars([_star_from_json(star) for star in map]) for map in data]
        )

    def __repr__(self) -> str:
        return f"AkuChapters({self.chapters})"
