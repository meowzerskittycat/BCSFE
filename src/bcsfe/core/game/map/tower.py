from __future__ import annotations
from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.game.map.chapters import Chapters
from bcsfe.core.io.schema import Bool, Grid, Section, Struct, field


@dataclass
class TowerChapters(Struct):
    chapters: Chapters = field(Section(Chapters))
    item_obtain_states: list[list[bool]] = field(Grid(Bool), part="item_obtain_states")

    def get_total_stars(self, chapter_id: int) -> int:
        return len(self.chapters.chapters[chapter_id].chapters)

    def get_total_stages(self, chapter_id: int, star: int) -> int:
        return len(self.chapters.chapters[chapter_id].chapters[star].stages)

    @staticmethod
    def edit_towers(save_file: core.SaveFile):
        towers = save_file.tower
        towers.chapters.edit_chapters(save_file, "V", 7000)
