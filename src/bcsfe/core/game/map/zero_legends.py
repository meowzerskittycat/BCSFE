from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from bcsfe import core
from bcsfe.cli import edits, color
from bcsfe.core.io.schema import (
    I8,
    I16,
    Array,
    Nested,
    Struct,
    field,
    transient,
)


@dataclass
class Stage(Struct):
    __transparent__: ClassVar[bool] = True
    clear_times: int = field(I16)

    def clear_stage(self, clear_amount: int = 1, ensure_cleared_only: bool = False):
        if ensure_cleared_only:
            self.clear_times = self.clear_times or clear_amount
        else:
            self.clear_times = clear_amount

    def unclear_stage(self):
        self.clear_times = 0


@dataclass
class Chapter(Struct):
    selected_stage: int = field(I8)
    clear_progress: int = field(I8)
    unlock_state: int = field(I8)
    stages: list[Stage] = field(Array(Nested(Stage), I16))
    total_stages: int = transient(int)

    def clear_stage(
        self,
        index: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        if overwrite_clear_progress:
            self.clear_progress = index + 1
        else:
            self.clear_progress = max(self.clear_progress, index + 1)
        self.stages[index].clear_stage(clear_amount, ensure_cleared_only)
        self.unlock_state = 3
        if index == self.total_stages - 1:
            return True
        return False

    def unclear_stage(self, index: int) -> bool:
        self.clear_progress = min(self.clear_progress, index)
        self.stages[index].unclear_stage()
        return True


@dataclass
class ChaptersStars(Struct):
    unknown: int = field(I8)
    chapters: list[Chapter] = field(Array(Nested(Chapter), I8))

    def clear_stage(
        self,
        star: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        finished = self.chapters[star].clear_stage(
            stage, clear_amount, overwrite_clear_progress, ensure_cleared_only
        )
        if finished:
            if star + 1 < len(self.chapters):
                self.chapters[star + 1].unlock_state = 1
        return finished

    def unclear_stage(self, star: int, stage: int) -> bool:
        finished = self.chapters[star].unclear_stage(stage)
        if finished and star + 1 < len(self.chapters):
            for chapter in self.chapters[star + 1 :]:
                chapter.unlock_state = 0
        return finished


@dataclass
class ZeroLegendsChapters(Struct):
    """Zero Legends, and (stored the same way) the Catclaw Championships."""

    __transparent__: ClassVar[bool] = True
    chapters: list[ChaptersStars] = field(Array(Nested(ChaptersStars), I16))

    def clear_stage(
        self,
        map: int,
        star: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        self.create(map)
        finished = self.chapters[map].clear_stage(
            star, stage, clear_amount, overwrite_clear_progress, ensure_cleared_only
        )
        if finished and map + 1 < len(self.chapters):
            self.chapters[map + 1].chapters[0].unlock_state = 1

        return finished

    def unclear_stage(self, map: int, star: int, stage: int) -> bool:
        self.create(map)
        finished = self.chapters[map].unclear_stage(star, stage)
        if finished and map + 1 < len(self.chapters) and star == 0:
            for chapter in self.chapters[map + 1].chapters:
                chapter.unlock_state = 0

        return finished

    def get_total_stars(self, chapter_id: int) -> int:
        return len(self.chapters[chapter_id].chapters)

    def get_total_stages(self, chapter_id: int, star: int) -> int:
        return len(self.chapters[chapter_id].chapters[star].stages)

    def create(self, chapter_id: int):
        diff = chapter_id - len(self.chapters)

        if diff >= 0:
            # new maps are shaped like the first one; each stage and star
            # must be its own object, or clearing one clears them all
            total_stars = self.get_total_stars(0) if self.chapters else 0
            total_stages = self.get_total_stages(0, 0) if total_stars else 0
            for _ in range(diff + 1):
                chapters = [
                    Chapter(0, 0, 0, [Stage(0) for _ in range(total_stages)])
                    for _ in range(total_stars)
                ]
                self.chapters.append(ChaptersStars(0, chapters))

    @staticmethod
    def edit_zero_legends(save_file: core.SaveFile):
        color.color_print_key("zero_legends_warning")
        zero_legends_chapters = save_file.zero_legends
        zero_legends_chapters.edit_chapters(save_file, "ND", base_index=34000)

    @staticmethod
    def edit_catclaw_championships(save_file: core.SaveFile):
        zero_legends_chapters = save_file.dojo_chapters
        zero_legends_chapters.edit_chapters(save_file, "G", 37000, True)

    def edit_chapters(
        self,
        save_file: core.SaveFile,
        letter_code: str,
        base_index: int,
        no_r_prefix: bool = False,
    ):
        edits.map.edit_chapters(
            save_file, self, letter_code, no_r_prefix=no_r_prefix, base_index=base_index
        )

    def unclear_rest(self, stages: list[int], stars: int, id: int):
        if not stages:
            return
        for star in range(stars, self.get_total_stars(id)):
            for stage in range(max(stages), self.get_total_stages(id, star)):
                self.chapters[id].chapters[star].stages[stage].clear_times = 0
                self.chapters[id].chapters[star].clear_progress = 0

    def set_total_stages(self, map: int, total_stages: int):
        self.create(map)
        for chapter in self.chapters[map].chapters:
            chapter.total_stages = total_stages
