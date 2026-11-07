"""Legend quest: laid out like gauntlets, but the map count is a byte, every
stage also records its attempts, and the stage ids follow at the end."""

from typing import Any, ClassVar

from bcsfe import core
from bcsfe.core.game.map.gauntlets import GauntletChapters
from bcsfe.core.game.map.stage_grid import MapStars, Stage, Star
from bcsfe.core.io.schema import I8, I16, Codec

__all__ = ["LegendQuestChapters", "ChaptersStars", "Chapter", "Stage"]

ChaptersStars = MapStars
Chapter = Star


class LegendQuestChapters(GauntletChapters):
    MAP_COUNT: ClassVar[Codec[int]] = I8
    TRIES: ClassVar[Codec[int] | None] = I16

    def __init__(self, chapters: list[MapStars], unknown: list[int], ids: list[int]):
        super().__init__(chapters, unknown)
        self.ids = ids
        # Every legend quest stage records attempts, so make sure it counts.
        for map in chapters:
            for star in map.chapters:
                for stage in star.stages:
                    if stage.tries is None:
                        stage.tries = 0

    @classmethod
    def init(cls) -> LegendQuestChapters:
        return LegendQuestChapters([], [], [])

    @staticmethod
    def read(data: core.Data) -> LegendQuestChapters:
        maps, total_stages, unknown = LegendQuestChapters._read_maps(data)
        ids = [data.read_int() for _ in range(total_stages)]
        return LegendQuestChapters(maps, unknown, ids)

    def write(self, data: core.Data):
        self._write_maps(data)
        for id in self.ids:
            data.write_int(id)

    def serialize(self) -> dict[str, Any]:
        return {**super().serialize(), "ids": self.ids}

    @staticmethod
    def deserialize(data: dict[str, Any]) -> LegendQuestChapters:
        base = GauntletChapters.deserialize(data)
        return LegendQuestChapters(base.chapters, base.unknown, data.get("ids", []))

    def __repr__(self) -> str:
        return f"LegendQuestChapters({self.chapters}, {self.unknown}, {self.ids})"
