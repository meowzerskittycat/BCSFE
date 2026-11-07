"""Story chapters (Empire of Cats, Into the Future, Cats of the Cosmos).

There are always 10 chapters with 51 stages each; chapter 3 is unused. Like
the other stage sections, the values are stored column by column: one value
per chapter (or per stage of every chapter) at a time, all as ints.
"""

from typing import Any

from bcsfe import core

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
    def convert_stage_id(index: int) -> int:
        if index == 46:
            return 46
        if index == 47:
            return 47
        index = 45 - index
        return index

    @staticmethod
    def get_chapter_type_from_index(index: int) -> int:
        if index < 3:
            return 0
        if index < 6:
            return 1
        return 2


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
