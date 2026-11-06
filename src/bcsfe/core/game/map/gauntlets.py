"""Gauntlets, collab gauntlets, behemoth culling and enigma clears.

Counts are given once at the start; per-star values are bytes and stage
clear counts are shorts. A byte per map follows whose meaning isn't known.
"""

from typing import Any, ClassVar

from bcsfe import core
from bcsfe.cli import edits
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.game.map.stage_grid import MapStars, Stage, Star
from bcsfe.core.io.schema import I8, I16, Codec

__all__ = ["GauntletChapters", "ChaptersStars", "Chapter", "Stage"]

ChaptersStars = MapStars
Chapter = Star


class GauntletChapters(grid.Maps):
    MAP_COUNT: ClassVar[Codec[int]] = I16
    TRIES: ClassVar[Codec[int] | None] = None

    def __init__(self, chapters: list[MapStars], unknown: list[int]):
        self.chapters = chapters
        self.unknown = unknown

    @classmethod
    def init(cls) -> GauntletChapters:
        return GauntletChapters([], [])

    @classmethod
    def _read_maps(cls, data: core.Data) -> tuple[list[MapStars], int, list[int]]:
        total_maps = cls.MAP_COUNT.read(data)
        total_stages = data.read_byte()
        total_stars = data.read_byte()

        maps = grid.read_selected(data, total_maps, total_stars, I8)
        grid.read_column(data, maps, "clear_progress", I8)
        grid.read_stages(data, maps, total_stages, I16, tries=cls.TRIES)
        grid.read_column(data, maps, "chapter_unlock_state", I8)
        unknown = [data.read_byte() for _ in range(total_maps)]
        return maps, total_stages, unknown

    def _write_maps(self, data: core.Data):
        total_maps, total_stages, total_stars = grid.dims(self.chapters)
        self.MAP_COUNT.write(data, total_maps)
        data.write_byte(total_stages)
        data.write_byte(total_stars)

        grid.write_selected(data, self.chapters, I8)
        grid.write_column(data, self.chapters, "clear_progress", I8)
        grid.write_stages(data, self.chapters, I16, tries=self.TRIES)
        grid.write_column(data, self.chapters, "chapter_unlock_state", I8)
        for unknown in self.unknown:
            data.write_byte(unknown)

    @staticmethod
    def read(data: core.Data) -> GauntletChapters:
        maps, _, unknown = GauntletChapters._read_maps(data)
        return GauntletChapters(maps, unknown)

    def write(self, data: core.Data):
        self._write_maps(data)

    def serialize(self) -> dict[str, Any]:
        return {
            "chapters": [map.to_json() for map in self.chapters],
            "unknown": self.unknown,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> GauntletChapters:
        maps = [MapStars.from_json(map) for map in data.get("chapters", [])]
        return GauntletChapters(maps, data.get("unknown", []))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.chapters}, {self.unknown})"

    @staticmethod
    def edit_gauntlets(save_file: core.SaveFile):
        save_file.gauntlets.edit_chapters(save_file, "A", 24000)

    @staticmethod
    def edit_collab_gauntlets(save_file: core.SaveFile):
        save_file.collab_gauntlets.edit_chapters(save_file, "CA", 27000)

    @staticmethod
    def edit_behemoth_culling(save_file: core.SaveFile):
        save_file.behemoth_culling.edit_chapters(save_file, "Q", 31000)

    @staticmethod
    def edit_enigma_stages(save_file: core.SaveFile):
        save_file.enigma_clears.edit_chapters(save_file, "H", 25000)

    def edit_chapters(
        self, save_file: core.SaveFile, letter_code: str, base_index: int
    ):
        edits.map.edit_chapters(save_file, self, letter_code, base_index=base_index)
