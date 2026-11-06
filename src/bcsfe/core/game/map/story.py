"""Story chapters (Empire of Cats, Into the Future, Cats of the Cosmos).

There are always 10 chapters with 51 stages each; chapter 3 is unused. Like
the other stage sections, the values are stored column by column: one value
per chapter (or per stage of every chapter) at a time, all as ints.
"""

import random
from typing import Any

from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt

TOTAL_CHAPTERS = 10
TOTAL_STAGES = 51
# Only the first 49 stages store a treasure, and only 48 are real stages.
TREASURE_STAGES = 49
VALID_TREASURE_STAGES = 48
# Chapters whose stages store an Into the Future timed score.
ITF_CHAPTERS = range(4, 7)

_TREASURE_FESTIVAL = (
    "time_until_treasure_chance",
    "treasure_chance_duration",
    "treasure_chance_value",
    "treasure_chance_stage_id",
    "treasure_festival_type",
)


class Stage:
    def __init__(self, clear_times: int = 0):
        self.clear_times = clear_times
        self.treasure = 0
        self.itf_timed_score = 0

    @staticmethod
    def init() -> Stage:
        return Stage()

    def serialize(self) -> dict[str, Any]:
        return {
            "clear_times": self.clear_times,
            "treasure": self.treasure,
            "itf_timed_score": self.itf_timed_score,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Stage:
        stage = Stage(data.get("clear_times", 0))
        stage.treasure = data.get("treasure", 0)
        stage.itf_timed_score = data.get("itf_timed_score", 0)
        return stage

    def __repr__(self) -> str:
        return f"Stage({self.clear_times}, {self.treasure}, {self.itf_timed_score})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Stage) and vars(self) == vars(other)

    def clear_stage(self, clear_amount: int = 1):
        self.clear_times = clear_amount

    def unclear_stage(self):
        self.clear_times = 0

    def is_cleared(self) -> bool:
        return self.clear_times > 0

    def set_treasure(self, treasure: int):
        self.treasure = treasure


class Chapter:
    def __init__(self, selected_stage: int = 0):
        self.selected_stage = selected_stage
        self.progress = 0
        self.stages = [Stage() for _ in range(TOTAL_STAGES)]
        self.time_until_treasure_chance = 0
        self.treasure_chance_duration = 0
        self.treasure_chance_value = 0
        self.treasure_chance_stage_id = 0
        self.treasure_festival_type = 0

    @staticmethod
    def init() -> Chapter:
        return Chapter()

    def clear_stage(
        self,
        index: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
    ):
        if overwrite_clear_progress:
            self.progress = index + 1
        else:
            self.progress = max(self.progress, index + 1)
        self.stages[index].clear_stage(clear_amount)

    def set_treasure(self, stage_id: int, treasure: int):
        self.stages[stage_id].set_treasure(treasure)

    def is_stage_clear(self, stage_id: int) -> bool:
        return self.stages[stage_id].is_cleared()

    def get_treasure_stages(self) -> list[Stage]:
        return self.stages[:TREASURE_STAGES]

    def get_valid_treasure_stages(self) -> list[Stage]:
        return self.stages[:VALID_TREASURE_STAGES]

    def apply_progress(self, progress: int, clear_times: list[int] | None = None):
        if clear_times is None:
            clear_times = [1] * progress

        self.progress = progress
        for i in range(progress + 1, VALID_TREASURE_STAGES):
            self.stages[i].unclear_stage()

        for i in range(progress):
            self.stages[i].clear_stage(clear_times[i])

    def clear_chapter(self):
        self.apply_progress(VALID_TREASURE_STAGES)

    def serialize(self) -> dict[str, Any]:
        return {
            "selected_stage": self.selected_stage,
            "progress": self.progress,
            "stages": [stage.serialize() for stage in self.stages],
            **{name: getattr(self, name) for name in _TREASURE_FESTIVAL},
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Chapter:
        chapter = Chapter(data.get("selected_stage", 0))
        chapter.progress = data.get("progress", 0)
        chapter.stages = [Stage.deserialize(stage) for stage in data.get("stages", [])]
        for name in _TREASURE_FESTIVAL:
            setattr(chapter, name, data.get(name, 0))
        return chapter

    def __repr__(self) -> str:
        values = ", ".join(str(getattr(self, name)) for name in _TREASURE_FESTIVAL)
        return (
            f"Chapter({self.selected_stage}, {self.progress}, {self.stages}, {values})"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Chapter) and vars(self) == vars(other)


def _read_column(stream: core.Data, objects: list[Any], attr: str):
    for obj in objects:
        setattr(obj, attr, stream.read_int())


def _write_column(stream: core.Data, objects: list[Any], attr: str):
    for obj in objects:
        stream.write_int(getattr(obj, attr))


class StoryChapters:
    def __init__(self, chapters: list[Chapter]):
        self.chapters = chapters

    @staticmethod
    def init() -> StoryChapters:
        return StoryChapters([Chapter() for _ in range(TOTAL_CHAPTERS)])

    def get_real_chapters(self) -> list[Chapter]:
        """Every chapter except the unused one."""
        return [chapter for i, chapter in enumerate(self.chapters) if i != 3]

    def clear_stage(
        self,
        map: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        chapters: list[Chapter] | None = None,
    ):
        if chapters is None:
            chapters = self.chapters
        chapters[map].clear_stage(stage, clear_amount, overwrite_clear_progress)

    def set_treasure(self, chapter: int, stage: int, treasure: int):
        self.chapters[chapter].set_treasure(stage, treasure)

    def is_stage_clear(self, chapter: int, stage: int) -> bool:
        return self.chapters[chapter].is_stage_clear(stage)

    # --- binary layout -----------------------------------------------------

    @staticmethod
    def read(stream: core.Data) -> StoryChapters:
        story = StoryChapters([Chapter() for _ in range(TOTAL_CHAPTERS)])
        _read_column(stream, story.chapters, "selected_stage")
        _read_column(stream, story.chapters, "progress")
        for chapter in story.chapters:
            chapter.stages = [Stage(stream.read_int()) for _ in range(TOTAL_STAGES)]
        for chapter in story.chapters:
            _read_column(stream, chapter.get_treasure_stages(), "treasure")
        return story

    def write(self, stream: core.Data):
        _write_column(stream, self.chapters, "selected_stage")
        _write_column(stream, self.chapters, "progress")
        for chapter in self.chapters:
            _write_column(stream, chapter.stages, "clear_times")
        for chapter in self.chapters:
            _write_column(stream, chapter.get_treasure_stages(), "treasure")

    def read_treasure_festival(self, stream: core.Data):
        for name in _TREASURE_FESTIVAL:
            _read_column(stream, self.chapters, name)

    def write_treasure_festival(self, stream: core.Data):
        for name in _TREASURE_FESTIVAL:
            _write_column(stream, self.chapters, name)

    def read_itf_timed_scores(self, stream: core.Data):
        for i in ITF_CHAPTERS:
            _read_column(stream, self.chapters[i].stages, "itf_timed_score")

    def write_itf_timed_scores(self, stream: core.Data):
        for i in ITF_CHAPTERS:
            _write_column(stream, self.chapters[i].stages, "itf_timed_score")

    def serialize(self) -> list[dict[str, Any]]:
        return [chapter.serialize() for chapter in self.chapters]

    @staticmethod
    def deserialize(data: list[dict[str, Any]]) -> StoryChapters:
        return StoryChapters([Chapter.deserialize(chapter) for chapter in data])

    def __repr__(self) -> str:
        return f"StoryChapters({self.chapters})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StoryChapters) and self.chapters == other.chapters

    @staticmethod
    def clear_tutorial(save_file: core.SaveFile):
        save_file.tutorial_state = max(save_file.tutorial_state, 1)
        save_file.koreaSuperiorTreasureState = max(
            save_file.koreaSuperiorTreasureState, 2
        )
        save_file.ui6 = max(save_file.ui6, 1)
        new_length = len(save_file.new_dialogs_2)
        if new_length < 6:
            save_file.new_dialogs_2.extend([0] * (6 - new_length))

        save_file.new_dialogs_2[1] = max(save_file.new_dialogs_2[1], 2)
        save_file.new_dialogs_2[5] = max(save_file.new_dialogs_2[5], 2)
        if save_file.story.chapters[0].stages[0].clear_times == 0:
            save_file.story.clear_stage(0, 0)

    @staticmethod
    def get_chapter_names(
        save_file: core.SaveFile, chapter_ids: list[int] | None = None
    ) -> list[str] | None:
        if chapter_ids is None:
            chapter_ids = [0, 1, 2, 3, 4, 5, 6, 7, 8]

        chapter_names: list[str] = []
        localizable = core.core_data.get_localizable(save_file)
        eoc_name = localizable.get("everyplay_mapname_J")
        itf_name = localizable.get("everyplay_mapname_W")
        cotc_name = localizable.get("everyplay_mapname_P")
        if eoc_name is None or itf_name is None or cotc_name is None:
            return None

        for chapter_id in chapter_ids:
            if chapter_id < 3:
                chapter_names.append(eoc_name.replace("%d", str(chapter_id + 1)))
            elif chapter_id < 6:
                chapter_names.append(itf_name.replace("%d", str(chapter_id - 2)))
            else:
                chapter_names.append(cotc_name.replace("%d", str(chapter_id - 5)))

        return chapter_names

    @staticmethod
    def select_story_chapters(
        save_file: core.SaveFile, chapters: list[int] | None = None
    ) -> list[int] | None:
        chapter_names = StoryChapters.get_chapter_names(save_file, chapters)

        if chapter_names is None:
            return None

        selected_chapters = prompt.choose_many(chapter_names, "select_story_chapters")

        return selected_chapters

    @staticmethod
    def get_selected_chapter_progress(max_stages: int = 48) -> int | None:
        progress = prompt.number(
            "edit_chapter_progress_all",
            min=0,
            max=prompt.MaxValue.always_cap(max_stages),
        )
        if progress is None:
            return None

        return progress

    @staticmethod
    def edit_chapter_progress(
        save_file: core.SaveFile,
        chapter_id: int,
        chapter_name: str,
        clear_amount: int,
        clear_amount_choose: int,
    ) -> bool:
        max_stages = 48
        chapter = save_file.story.get_real_chapters()[chapter_id]
        progress = prompt.number(
            "edit_chapter_progress",
            min=0,
            max=prompt.MaxValue.always_cap(max_stages),
            chapter_name=chapter_name,
        )
        if progress is None:
            return False
        clear_amounts = [1] * progress
        if clear_amount_choose == 0:
            clear_amount2 = core.EventChapters.ask_clear_amount()
            if clear_amount2 is None:
                return False
            clear_amounts = [clear_amount2] * progress
        elif clear_amount_choose == 1:
            clear_amounts = [clear_amount] * progress
        elif clear_amount_choose == 2:
            for i in range(progress):
                StoryChapters.print_current_stage(save_file, chapter_id, i)
                clear_amount2 = core.EventChapters.ask_clear_amount()
                if clear_amount2 is None:
                    return False
                clear_amounts[i] = clear_amount2

        chapter.apply_progress(progress, clear_amounts)
        return progress != 0

    @staticmethod
    def convert_stage_id(index: int) -> int:
        if index == 46:
            return 46
        if index == 47:
            return 47
        index = 45 - index
        return index

    @staticmethod
    def ask_clear_count() -> int | None:
        clear_count = prompt.number(
            "edit_stage_clear_count",
            min=0,
            max=prompt.MaxValue.i16(core.core_data.max_value_manager.stage_clear_count),
        )

        return clear_count

    @staticmethod
    def ask_if_individual_clear_counts() -> bool | None:
        return dialog_creator.single_select_key(
            dialog_creator.Actions[bool]
            .new()
            .add_new_key("individual_clear_counts", lambda _: True)
            .add_new_key("all_clear_counts", lambda _: False),
            "individual_clear_counts_dialog",
        )

    @staticmethod
    def edit_stage_clear_count(
        save_file: core.SaveFile, chapter_id: int, stage_id: int
    ):
        chapter = save_file.story.get_real_chapters()[chapter_id]
        stage = chapter.stages[stage_id]
        clear_count = StoryChapters.ask_clear_count()
        if clear_count is None:
            return
        stage.clear_times = clear_count

    def clear_previous_chapters(self, chapter_id: int):
        chapters = self.get_real_chapters()
        """
        0: eoc 1
        1: eoc 2 - requires eoc 1
        2: eoc 3 - requires eoc 1 + eoc 2
        3: itf 1 - requires eoc 1
        4: itf 2 - requires eoc 1 + itf 1
        5: itf 3 - requires eoc 1 + itf 1 + itf 2
        6: cotc 1 - requires eoc 1 + itf 1
        7: cotc 2 - requires eoc 1 + itf 1 + cotc 1
        8: cotc 3 - requires eoc 1 + itf 1 + cotc 1 + cotc 2

        """
        if chapter_id == 1:  # eoc 2
            chapters[0].clear_chapter()
        elif chapter_id == 2:  # eoc 3
            chapters[0].clear_chapter()
            chapters[1].clear_chapter()
        elif chapter_id == 3:  # itf 1
            chapters[0].clear_chapter()
        elif chapter_id == 4:  # itf 2
            chapters[0].clear_chapter()
            chapters[3].clear_chapter()
        elif chapter_id == 5:  # itf 3
            chapters[0].clear_chapter()
            chapters[3].clear_chapter()
            chapters[4].clear_chapter()
        elif chapter_id == 6:  # cotc 1
            chapters[0].clear_chapter()
            chapters[3].clear_chapter()
        elif chapter_id == 7:  # cotc 2
            chapters[0].clear_chapter()
            chapters[3].clear_chapter()
            chapters[6].clear_chapter()
        elif chapter_id == 8:  # cotc 3
            chapters[0].clear_chapter()
            chapters[3].clear_chapter()
            chapters[6].clear_chapter()
            chapters[7].clear_chapter()

    @staticmethod
    def print_current_chapter(save_file: core.SaveFile, chapter_id: int):
        chapter_names = StoryChapters.get_chapter_names(save_file)
        if chapter_names is None:
            return
        chapter_name = chapter_names[chapter_id]
        color.color_print_key("current_chapter", chapter_name=chapter_name)

    @staticmethod
    def print_current_treasure_group(
        save_file: core.SaveFile, chapter_id: int, treasure_group_id: int
    ):
        chapter_type = StoryChapters.get_chapter_type_from_index(chapter_id)

        treasure_group_names = TreasureGroupNames(
            save_file, chapter_type
        ).treasure_group_names
        if treasure_group_names is None:
            return
        treasure_group_name = treasure_group_names[treasure_group_id]
        color.color_print_key(
            "current_treasure_group", treasure_group_name=treasure_group_name
        )

    @staticmethod
    def clear_story(save_file: core.SaveFile):
        story = save_file.story
        story.edit_chapters(
            save_file,
        )

    def edit_chapters(self, save_file: core.SaveFile):
        chapters = self.get_real_chapters()
        names = StoryChapters.get_chapter_names(save_file)
        if names is None:
            return

        map_choices = StoryChapters.select_story_chapters(save_file)
        if not map_choices:
            return

        clear_type_choice = prompt.choose(
            prompt.keys(["clear_whole_chapters", "clear_specific_stages"]),
            dialog="select_clear_type",
        )
        if clear_type_choice is None:
            return

        modify_clear_amounts = prompt.confirm("modify_clear_amounts")
        if modify_clear_amounts is None:
            return
        clear_amount = 1
        clear_amount_type = -1
        if modify_clear_amounts:
            if len(map_choices) == 1:
                clear_amount_type = 0
            else:
                options = ["clear_amount_chapter", "clear_amount_all"]
                if clear_type_choice == 1:
                    options.append("clear_amount_stages")
                clear_amount_type = prompt.choose(
                    prompt.keys(options), dialog="select_clear_amount_type"
                )
                if clear_amount_type is None:
                    return

            if clear_amount_type == 1:
                clear_amount = core.EventChapters.ask_clear_amount()
                if clear_amount is None:
                    return

        for id in map_choices:
            stage_names = StageNames(
                save_file, chapter=str(self.get_chapter_type_from_index(id))
            )
            stage_names = stage_names.stage_names
            if stage_names is None:
                return

            new_stage_names: list[str] = []
            for i in range(48):
                index_stage_id = StoryChapters.convert_stage_id(i)
                new_stage_names.append(stage_names[index_stage_id])
            stage_names = new_stage_names
            map_name = names[id]
            color.color_print_key("current_sol_chapter", name=map_name, id=id)
            if clear_type_choice:
                stages = core.EventChapters.ask_stages_stage_names(stage_names)
                if stages is None:
                    return
            else:
                stages = list(range(48))

            if clear_amount_type == 0:
                clear_amount = core.EventChapters.ask_clear_amount()
                if clear_amount is None:
                    return

            could_unclear_stages = False

            if chapters[id].progress > max(stages) + 1:
                could_unclear_stages = True

            for stage in range(max(stages) + 1, 48):
                if chapters[id].stages[stage].clear_times:
                    could_unclear_stages = True

            if could_unclear_stages:
                unclear_other_stages = prompt.confirm("unclear_other_stages")
                if unclear_other_stages is None:
                    return
            else:
                unclear_other_stages = False

            if unclear_other_stages:
                chapters[id].progress = 0
                for stage in range(max(stages), 48):
                    chapters[id].stages[stage].clear_times = 0

            for stage in stages:
                if clear_amount_type == 2:
                    stage_name = stage_names[stage]
                    color.color_print_key(
                        "current_sol_stage", name=stage_name, id=stage
                    )
                if clear_amount_type == 2:
                    clear_amount = core.EventChapters.ask_clear_amount()
                    if clear_amount is None:
                        return
                self.clear_stage(
                    id,
                    stage,
                    overwrite_clear_progress=True,
                    clear_amount=clear_amount,
                    chapters=chapters,
                )

        color.color_print_key("map_chapters_edited")

    @staticmethod
    def custom_treasure_level() -> int | None:
        max_treasure_level = core.core_data.max_value_manager.treasure_level
        treasure_level = prompt.number(
            "custom_treasure_level_dialog",
            min=0,
            max=prompt.MaxValue.i32(max_treasure_level),
        )
        if treasure_level is None:
            return None
        return treasure_level

    @staticmethod
    def ask_treasure_level(save_file: core.SaveFile) -> int | None:
        treasure_text = core.core_data.get_treasure_text(save_file).treasure_text
        if treasure_text is None:
            return None

        return dialog_creator.single_select_key(
            dialog_creator.Actions[int | None]
            .new()
            .add_new_key("no_treasure", lambda _: 0)
            .add_new_raw(treasure_text[:3], lambda v: v + 1)
            .add_new_key(
                "custom_treasure_level", lambda _: StoryChapters.custom_treasure_level()
            ),
            "treasure_level_dialog",
        )

    @staticmethod
    def is_per_chapter(chapters: list[int]) -> bool | None:
        if len(chapters) == 1:
            return True

        return dialog_creator.single_select_key(
            dialog_creator.Actions[bool]
            .new()
            .add_new_key("per_chapter", lambda _: True)
            .add_new_key("all_selected_chapters", lambda _: False),
            "edit_per_chapter",
        )

    @staticmethod
    def edit_treasures_whole_chapters(save_file: core.SaveFile, chapters: list[int]):
        is_per_chapter = StoryChapters.is_per_chapter(chapters)
        if is_per_chapter is None:
            return

        if is_per_chapter:
            for chapter_id in chapters:
                StoryChapters.print_current_chapter(save_file, chapter_id)
                chapter = save_file.story.get_real_chapters()[chapter_id]
                treasure_level = StoryChapters.ask_treasure_level(save_file)
                if treasure_level is None:
                    return
                for stage in chapter.get_valid_treasure_stages():
                    stage.set_treasure(treasure_level)
        else:
            treasure_level = StoryChapters.ask_treasure_level(save_file)
            if treasure_level is None:
                return
            for chapter_id in chapters:
                chapter = save_file.story.get_real_chapters()[chapter_id]
                for stage in chapter.get_valid_treasure_stages():
                    stage.set_treasure(treasure_level)

    @staticmethod
    def get_chapter_type_from_index(index: int) -> int:
        if index < 3:
            return 0
        if index < 6:
            return 1
        return 2

    @staticmethod
    def select_stages_by_id() -> list[int] | None:
        stage_ids = prompt.numbers("select_stage_id", min=1, max=48)
        if stage_ids is None:
            return None
        stage_ids = [stage_id - 1 for stage_id in stage_ids]
        return stage_ids

    @staticmethod
    def select_stage_by_name(
        save_file: core.SaveFile, chapter_id: int
    ) -> list[int] | None:
        chapter_type = StoryChapters.get_chapter_type_from_index(chapter_id)
        stage_names = StageNames(save_file, str(chapter_type)).stage_names
        if not stage_names:
            return None
        new_stage_names: list[str] = []
        for i in range(48):
            index_stage_id = StoryChapters.convert_stage_id(i)
            new_stage_names.append(stage_names[index_stage_id])
        selected_stages = prompt.choose_many(
            new_stage_names, dialog="select_stages_name"
        )

        if not selected_stages:
            return None

        return selected_stages

    @staticmethod
    def select_stages(save_file: core.SaveFile, chapter_id: int) -> list[int] | None:
        return dialog_creator.single_select_key(
            dialog_creator.Actions[list[int] | None]
            .new()
            .add_new_key(
                "select_stage_by_id", lambda _: StoryChapters.select_stages_by_id()
            )
            .add_new_key(
                "select_stage_by_name",
                lambda _: StoryChapters.select_stage_by_name(save_file, chapter_id),
            ),
            "select_stage_dialog",
        )

    @staticmethod
    def edit_treasures_individual_stages(save_file: core.SaveFile, chapters: list[int]):
        is_per_chapter = StoryChapters.is_per_chapter(chapters)
        if is_per_chapter is None:
            return
        if is_per_chapter:
            for chapter_id in chapters:
                StoryChapters.print_current_chapter(save_file, chapter_id)
                chapter = save_file.story.get_real_chapters()[chapter_id]
                stage_ids = StoryChapters.select_stages(save_file, chapter_id)
                if stage_ids is None:
                    return
                treasure_level = StoryChapters.ask_treasure_level(save_file)
                if treasure_level is None:
                    return
                for stage_id in stage_ids:
                    real_stage_id = StoryChapters.convert_stage_id(stage_id)
                    chapter.set_treasure(real_stage_id, treasure_level)
        else:
            stage_ids = StoryChapters.select_stages(save_file, 0)
            if stage_ids is None:
                return
            treasure_level = StoryChapters.ask_treasure_level(save_file)
            if treasure_level is None:
                return
            for chapter_id in chapters:
                chapter = save_file.story.get_real_chapters()[chapter_id]
                for stage_id in stage_ids:
                    real_stage_id = StoryChapters.convert_stage_id(stage_id)
                    chapter.set_treasure(real_stage_id, treasure_level)

    @staticmethod
    def edit_treasure_group_ind(
        save_file: core.SaveFile,
        chapter_id: int,
        treasure_group_data: list[list[int]],
        chapter: Chapter,
        selected_treasure_groups: list[int],
    ):
        for treasure_group_id in selected_treasure_groups:
            StoryChapters.print_current_treasure_group(
                save_file, chapter_id, treasure_group_id
            )
            treasure_level = StoryChapters.ask_treasure_level(save_file)
            if treasure_level is None:
                return
            treasure_group = treasure_group_data[treasure_group_id]
            for stage_id in treasure_group:
                chapter.set_treasure(stage_id, treasure_level)

    @staticmethod
    def edit_treasure_group_many(
        save_file: core.SaveFile,
        treasure_group_data: list[list[int]],
        chapter: Chapter,
        selected_treasure_groups: list[int],
    ):
        treasure_level = StoryChapters.ask_treasure_level(save_file)
        if treasure_level is None:
            return

        for treasure_group_id in selected_treasure_groups:
            treasure_group = treasure_group_data[treasure_group_id]
            for stage_id in treasure_group:
                chapter.set_treasure(stage_id, treasure_level)

    @staticmethod
    def edit_treasures_groups(save_file: core.SaveFile, chapters: list[int]):
        for chapter_id in chapters:
            StoryChapters.print_current_chapter(save_file, chapter_id)
            chapter = save_file.story.get_real_chapters()[chapter_id]
            chapter_type = StoryChapters.get_chapter_type_from_index(chapter_id)
            treasure_group_data = TreasureGroupData(
                save_file, chapter_type
            ).treasure_group_data
            treasure_group_names = TreasureGroupNames(
                save_file, chapter_type
            ).treasure_group_names
            if treasure_group_data is None or treasure_group_names is None:
                return
            treasure_group_names_new: list[str] = []
            for i in range(len(treasure_group_data)):
                treasure_group_names_new.append(treasure_group_names[i])

            selected_treasure_groups = prompt.choose_many(
                treasure_group_names_new, dialog="select_treasure_groups"
            )

            if selected_treasure_groups is None:
                return

            dialog_creator.single_select_key(
                dialog_creator.Actions[None]
                .new()
                .add_new_key(
                    "group_individual",
                    lambda _: StoryChapters.edit_treasure_group_ind(
                        save_file,
                        chapter_id,
                        treasure_group_data,  # type: ignore
                        chapter,
                        selected_treasure_groups,  # type: ignore
                    ),
                )
                .add_new_key(
                    "group_all_at_once",
                    lambda _: StoryChapters.edit_treasure_group_many(
                        save_file,
                        treasure_group_data,  # type: ignore
                        chapter,
                        selected_treasure_groups,  # type: ignore
                    ),
                ),
                "select_treasure_groups_individual",
            )

    @staticmethod
    def edit_treasures(save_file: core.SaveFile):
        selected_chapters = StoryChapters.select_story_chapters(save_file)
        if not selected_chapters:
            return
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "whole_chapters",
                lambda _: StoryChapters.edit_treasures_whole_chapters(
                    save_file, selected_chapters
                ),
            )
            .add_new_key(
                "individual_stages",
                lambda _: StoryChapters.edit_treasures_individual_stages(
                    save_file, selected_chapters
                ),
            )
            .add_new_key(
                "treasure_groups",
                lambda _: StoryChapters.edit_treasures_groups(
                    save_file, selected_chapters
                ),
            ),
            "treasure_dialog",
        )

        color.color_print_key("treasures_edited")

    @staticmethod
    def edit_itf_timed_scores(save_file: core.SaveFile):
        selected_chapters = StoryChapters.select_story_chapters(
            save_file, chapters=[3, 4, 5]
        )
        if not selected_chapters:
            return
        selected_chapters = [chapter_id + 3 for chapter_id in selected_chapters]
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "whole_chapters",
                lambda _: StoryChapters.edit_itf_timed_scores_whole_chapters(
                    save_file, selected_chapters
                ),
            )
            .add_new_key(
                "individual_stages",
                lambda _: StoryChapters.edit_itf_timed_scores_individual_stages(
                    save_file, selected_chapters
                ),
            ),
            "itf_timed_scores_dialog",
        )

        color.color_print_key("itf_timed_scores_edited")

    @staticmethod
    def itf_timed_score_input() -> tuple[int, int] | None:
        inp = prompt.text("itf_timed_score_dialog")
        if inp is None:
            return None

        parts = inp.split("-", maxsplit=1)

        parts_i: list[int] = []
        for part in parts:
            if not part.isdigit():
                return StoryChapters.itf_timed_score_input()
            score = int(part)
            mx = prompt.MaxValue.i32(core.core_data.max_value_manager.itf_timed_score)
            score = mx.clamp(score)
            parts_i.append(score)

        return min(parts_i), max(parts_i) + 1

    @staticmethod
    def edit_itf_timed_scores_whole_chapters(
        save_file: core.SaveFile, chapters: list[int]
    ):
        is_per_chapter = StoryChapters.is_per_chapter(chapters)
        if is_per_chapter is None:
            return

        if is_per_chapter:
            for chapter_id in chapters:
                StoryChapters.print_current_chapter(save_file, chapter_id)
                chapter = save_file.story.get_real_chapters()[chapter_id]
                score = StoryChapters.itf_timed_score_input()
                if score is None:
                    return
                for stage in chapter.get_valid_treasure_stages():
                    stage.itf_timed_score = random.randrange(score[0], score[1])
        else:
            score = StoryChapters.itf_timed_score_input()
            if score is None:
                return
            for chapter_id in chapters:
                chapter = save_file.story.get_real_chapters()[chapter_id]
                for stage in chapter.get_valid_treasure_stages():
                    stage.itf_timed_score = random.randrange(score[0], score[1])

    @staticmethod
    def print_current_stage(save_file: core.SaveFile, chapter_id: int, stage_id: int):
        chapter_names = StoryChapters.get_chapter_names(save_file)
        if chapter_names is None:
            return
        chapter_name = chapter_names[chapter_id]
        chapter_type = StoryChapters.get_chapter_type_from_index(chapter_id)
        stage_names = StageNames(save_file, str(chapter_type)).stage_names
        if stage_names is None:
            return
        stage_id = StoryChapters.convert_stage_id(stage_id)
        stage_name = stage_names[stage_id]
        color.color_print_key(
            "current_stage", chapter_name=chapter_name, stage_name=stage_name
        )

    @staticmethod
    def edit_itf_timed_scores_ind_per_chapter_ind(
        save_file: core.SaveFile,
        chapter: Chapter,
        chapter_id: int,
        stage_ids: list[int],
    ):
        for stage_id in stage_ids:
            StoryChapters.print_current_stage(save_file, chapter_id, stage_id)

            score = StoryChapters.itf_timed_score_input()

            if score is None:
                return
            chapter.stages[stage_id].itf_timed_score = random.randrange(
                score[0], score[1]
            )

    @staticmethod
    def edit_itf_timed_scores_ind_per_chapter_many(
        chapter: Chapter, stage_ids: list[int]
    ):
        score = StoryChapters.itf_timed_score_input()
        if score is None:
            return
        for stage_id in stage_ids:
            chapter.stages[stage_id].itf_timed_score = random.randrange(
                score[0], score[1]
            )

    @staticmethod
    def edit_itf_timed_scores_ind_per_chapter(
        save_file: core.SaveFile, chapters: list[int], is_ind: bool
    ):
        for chapter_id in chapters:
            StoryChapters.print_current_chapter(save_file, chapter_id)
            chapter = save_file.story.get_real_chapters()[chapter_id]
            stage_ids = StoryChapters.select_stages(save_file, chapter_id)
            if stage_ids is None:
                return
            if is_ind:
                StoryChapters.edit_itf_timed_scores_ind_per_chapter_ind(
                    save_file, chapter, chapter_id, stage_ids
                )
            else:
                StoryChapters.edit_itf_timed_scores_ind_per_chapter_many(
                    chapter, stage_ids
                )

    @staticmethod
    def edit_itf_timed_scores_ind_many(
        save_file: core.SaveFile, chapters: list[int], is_ind: bool
    ):
        stage_ids = StoryChapters.select_stages(save_file, 3)
        if stage_ids is None:
            return
        if is_ind:
            for stage_id in stage_ids:
                StoryChapters.print_current_stage(save_file, 3, stage_id)
                score = StoryChapters.itf_timed_score_input()
                if score is None:
                    return
                for chapter_id in chapters:
                    chapter = save_file.story.get_real_chapters()[chapter_id]
                    chapter.stages[stage_id].itf_timed_score = random.randrange(
                        score[0], score[1]
                    )
        else:
            score = StoryChapters.itf_timed_score_input()
            if score is None:
                return
            for chapter_id in chapters:
                chapter = save_file.story.get_real_chapters()[chapter_id]
                for stage_id in stage_ids:
                    chapter.stages[stage_id].itf_timed_score = random.randrange(
                        score[0], score[1]
                    )

    @staticmethod
    def edit_itf_timed_scores_individual_stages(
        save_file: core.SaveFile, chapters: list[int]
    ):
        is_per_chapter = StoryChapters.is_per_chapter(chapters)
        if is_per_chapter is None:
            return
        is_ind = dialog_creator.single_select_key(
            dialog_creator.Actions[bool]
            .new()
            .add_new_key("individual_stages", lambda _: True)
            .add_new_key("all_selected_stages", lambda _: False),
            "itf_timed_scores_individual_dialog",
        )
        if is_ind is None:
            return

        if is_per_chapter:
            StoryChapters.edit_itf_timed_scores_ind_per_chapter(
                save_file, chapters, is_ind
            )
        else:
            StoryChapters.edit_itf_timed_scores_ind_many(save_file, chapters, is_ind)


class StageNames:
    def __init__(self, save_file: core.SaveFile, chapter: str, max_stages: int = 48):
        self.save_file = save_file
        self.chapter = chapter
        self.max_stages = max_stages
        self.stage_names = self.get_stage_names()

    def get_file_name(self) -> str:
        if self.chapter.isdigit():
            return (
                f"StageName{self.chapter}_{core.core_data.get_lang(self.save_file)}.csv"
            )
        return f"StageName_{self.chapter}_{core.core_data.get_lang(self.save_file)}.csv"

    def get_stage_names(self) -> list[str] | None:
        file_name = self.get_file_name()
        gdg = core.core_data.get_game_data_getter(self.save_file)
        file = gdg.download("resLocal", file_name)
        if file is None:
            return None
        csv = core.CSV(
            file,
            delimiter=core.Delimeter.from_country_code_res(self.save_file.cc),
        )
        stage_names: list[str] = []
        if self.chapter.isdigit():
            for row in csv:
                stage_names.append(row[0].to_str())
        else:
            for row in csv:
                for value in row:
                    stage_names.append(value.to_str())
        return stage_names[: self.max_stages]

    def get_stage_name(self, stage_id: int) -> str | None:
        if self.stage_names is None:
            return None
        return self.stage_names[stage_id]


class TreasureText:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.treasure_text = self.get_treasure_text()

    def get_tt_file_name(self) -> str:
        return f"Treasure2_{core.core_data.get_lang(self.save_file)}.csv"

    def get_treasure_text(self) -> list[str] | None:
        file_name = self.get_tt_file_name()
        gdg = core.core_data.get_game_data_getter(self.save_file)
        file = gdg.download("resLocal", file_name)
        if file is None:
            return None
        csv = core.CSV(
            file,
            delimiter=core.Delimeter.from_country_code_res(self.save_file.cc),
        )
        treasure_text: list[str] = []
        for row in csv:
            treasure_text.append(row[0].to_str())
        return treasure_text


class TreasureGroupData:
    def __init__(self, save_file: core.SaveFile, chapter_type: int):
        self.save_file = save_file
        self.chapter_type = chapter_type
        self.treasure_group_data = self.get_treasure_group_data()

    def get_tgd_file_name(self) -> str:
        if self.chapter_type == 0:
            return "treasureData0.csv"
        if self.chapter_type == 1:
            return "treasureData1.csv"
        if self.chapter_type == 2:
            return "treasureData2_0.csv"
        return ""

    def get_treasure_group_data(self) -> list[list[int]] | None:
        gdg = core.core_data.get_game_data_getter(self.save_file)
        file = gdg.download("DataLocal", self.get_tgd_file_name())
        if file is None:
            return None
        csv = core.CSV(file)
        treasure_group_data: list[list[int]] = []
        for row in csv.lines[11:22]:
            treasure_group_data.append(
                [value.to_int() for value in row if value.to_int() != -1]
            )

        return treasure_group_data


class TreasureGroupNames:
    def __init__(self, save_file: core.SaveFile, chapter_type: int):
        self.save_file = save_file
        self.chapter_type = chapter_type
        self.treasure_group_names = self.get_treasure_group_names()

    def get_tgn_file_name(self) -> str:
        lang = core.core_data.get_lang(self.save_file)
        if self.chapter_type == 0:
            return f"Treasure3_0_{lang}.csv"
        if self.chapter_type == 1:
            return f"Treasure3_1_{lang}.csv"
        if self.chapter_type == 2:
            return f"Treasure3_2_0_{lang}.csv"
        return ""

    def get_treasure_group_names(self) -> list[str] | None:
        gdg = core.core_data.get_game_data_getter(self.save_file)
        file = gdg.download("resLocal", self.get_tgn_file_name())
        if file is None:
            return None
        csv = core.CSV(
            file,
            delimiter=core.Delimeter.from_country_code_res(self.save_file.cc),
        )
        treasure_group_names: list[str] = []
        for row in csv:
            treasure_group_names.append(row[0].to_str())
        return treasure_group_names
