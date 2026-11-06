"""Aku realm stages: only the selected stage and clear counts are stored,
and each star's stages are stored together (not interleaved)."""

from typing import Any

from bcsfe import core
from bcsfe.cli import color
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

    @staticmethod
    def edit_aku_chapters(save_file: core.SaveFile):
        aku = save_file.aku
        chapter = aku.chapters[0].chapters[0]

        clear_progress = core.StoryChapters.get_selected_chapter_progress(
            max_stages=len(chapter.stages)
        )
        if clear_progress is None:
            return

        if clear_progress > 1:
            individual_clear_count = core.StoryChapters.ask_if_individual_clear_counts()
            if individual_clear_count is None:
                return
        else:
            individual_clear_count = True

        if individual_clear_count:
            stage_names = core.StageNames(save_file, "DM", 49).stage_names
            if stage_names is None:
                return
            for i, stage in enumerate(chapter.stages[:clear_progress]):
                stage_name = stage_names[i]
                color.color_print_key("aku_current_stage", name=stage_name, id=i)
                clear_count = core.StoryChapters.ask_clear_count()
                if clear_count is None:
                    return
                stage.clear_stage(clear_count)
        else:
            clear_count = core.StoryChapters.ask_clear_count()
            if clear_count is None:
                return
            for stage in chapter.stages[:clear_progress]:
                stage.clear_stage(clear_count)

        for i in range(clear_progress, len(chapter.stages)):
            chapter.stages[i].clear_stage(0)

        color.color_print_key("aku_clear_success")
