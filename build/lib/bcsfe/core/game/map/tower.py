from dataclasses import dataclass

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
