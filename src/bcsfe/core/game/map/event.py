"""Event, Stories of Legend and collab stage progress.

Laid out like the main chapters but with one more level: map types (0 =
Stories of Legend, 1 = events, 2 = collabs, ...), each a list of maps. The
columns run over every map of every type in turn.
"""

from typing import Any

from bcsfe import core
from bcsfe.cli import color, dialog_creator, edits
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.game.map.stage_grid import MapStars, Stage, Star
from bcsfe.core.io.schema import I8, I16, I32, Codec

__all__ = ["EventChapters", "EventChapterGroup", "EventSubChapterStars"]

# Older names for the shared classes.
EventStage = Stage
EventSubChapter = Star
EventSubChapterStars = MapStars


class EventChapterGroup(grid.Maps):
    """The maps of one map type."""

    def __init__(self, chapters: list[MapStars]):
        self.chapters = chapters

    @staticmethod
    def init(total_subchapters: int, total_stars: int) -> EventChapterGroup:
        return EventChapterGroup(
            [MapStars.new(total_stars) for _ in range(total_subchapters)]
        )

    def serialize(self) -> list[dict[str, Any]]:
        return [
            {"chapters": map.to_json(), "legend_restriction": map.legend_restriction}
            for map in self.chapters
        ]

    @staticmethod
    def deserialize(data: list[dict[str, Any]]) -> EventChapterGroup:
        maps: list[MapStars] = []
        for map_data in data:
            map = MapStars.from_json(map_data.get("chapters", []))
            map.legend_restriction = map_data.get("legend_restriction", 0)
            maps.append(map)
        return EventChapterGroup(maps)

    def __repr__(self) -> str:
        return f"EventChapterGroup({self.chapters})"


# Before 8.1 every value is an int; old versions have fixed sizes and no
# counts, later ones repeat (types, maps, stars) before every column.
_FIXED_SIZES = {32: (3, 150, 3), 34: (4, 150, 3)}  # max version -> sizes
_FIXED_STAGES = 12


class EventChapters:
    def __init__(self, chapters: list[EventChapterGroup]):
        self.chapters = chapters
        self.chapter_completion_count: dict[int, int] = {}
        self.displayed_cleared_limit_text: dict[int, bool] = {}
        self.event_start_dates: dict[int, int] = {}
        self.stages_reward_claimed: list[int] = []

    def clear_stage(
        self,
        type: int,
        map: int,
        star: int,
        stage: int,
        clear_amount: int = 1,
        overwrite_clear_progress: bool = False,
        ensure_cleared_only: bool = False,
    ) -> bool:
        return self.chapters[type].clear_stage(
            map,
            star,
            stage,
            clear_amount,
            overwrite_clear_progress,
            ensure_cleared_only,
        )

    def unclear_stage(self, type: int, map: int, star: int, stage: int) -> bool:
        return self.chapters[type].unclear_stage(map, star, stage)

    def clear_map(self, type: int, map: int, star: int, increment: bool = True):
        self.chapters[type].clear_map(map, star, increment)

    def clear_chapter(self, type: int, map: int, increment: bool = True):
        self.chapters[type].clear_chapter(map, increment)

    def clear_group(self, type: int, increment: bool = True):
        self.chapters[type].clear_group(increment)

    def all_maps(self) -> list[MapStars]:
        return [map for group in self.chapters for map in group.chapters]

    @staticmethod
    def _fixed_sizes(gv: core.GameVersion) -> tuple[int, int, int] | None:
        for max_gv, sizes in _FIXED_SIZES.items():
            if gv <= max_gv:
                return sizes
        return None

    @staticmethod
    def init(gv: core.GameVersion) -> EventChapters:
        if gv < 20:
            return EventChapters([])
        types, maps, stars = EventChapters._fixed_sizes(gv) or (0, 0, 0)
        return EventChapters(
            [EventChapterGroup.init(maps, stars) for _ in range(types)]
        )

    @staticmethod
    def read(data: core.Data, gv: core.GameVersion) -> EventChapters:
        if gv < 20:
            return EventChapters([])

        compact = gv >= 80100
        fixed = EventChapters._fixed_sizes(gv)
        total_stages = 0
        if compact:
            types = data.read_byte()
            maps_per_type = data.read_short()
            stars = data.read_byte()
            total_stages = data.read_byte()
        elif fixed is not None:
            types, maps_per_type, stars = fixed
        else:
            types, maps_per_type, stars = (data.read_int() for _ in range(3))
        repeat = not compact and fixed is None

        small: Codec[int] = I8 if compact else I32
        stage_codec: Codec[int] = I16 if compact else I32

        groups = [
            EventChapterGroup(grid.read_selected(data, maps_per_type, stars, small))
            for _ in range(types)
        ]
        ev = EventChapters(groups)
        maps = ev.all_maps()

        if repeat:
            _skip_ints(data, 3)
        grid.read_column(data, maps, "clear_progress", small)

        if fixed is not None:
            total_stages = _FIXED_STAGES
        elif repeat:
            _skip_ints(data, 2)
            total_stages = data.read_int()
            _skip_ints(data, 1)
        grid.read_stages(data, maps, total_stages, stage_codec)

        if repeat:
            _skip_ints(data, 3)
        grid.read_column(data, maps, "chapter_unlock_state", small)
        return ev

    def get_lengths(self) -> tuple[int, int, int, int]:
        """(types, maps per type, stars per map, stages per star)."""
        maps_per_type, stages, stars = (
            grid.dims(self.chapters[0].chapters) if self.chapters else (0, 0, 0)
        )
        return len(self.chapters), maps_per_type, stars, stages

    def write(self, data: core.Data, gv: core.GameVersion):
        types, maps_per_type, stars, stages = self.get_lengths()
        compact = gv >= 80100
        repeat = not compact and gv > 34

        if compact:
            data.write_byte(types)
            data.write_short(maps_per_type)
            data.write_byte(stars)
            data.write_byte(stages)
        counts = [types, maps_per_type, stars]

        small: Codec[int] = I8 if compact else I32
        stage_codec: Codec[int] = I16 if compact else I32
        maps = self.all_maps()

        if repeat:
            _write_ints(data, counts)
        grid.write_selected(data, maps, small)

        if repeat:
            _write_ints(data, counts)
        grid.write_column(data, maps, "clear_progress", small)

        if repeat:
            _write_ints(data, [types, maps_per_type, stages, stars])
        grid.write_stages(data, maps, stage_codec)

        if repeat:
            _write_ints(data, counts)
        grid.write_column(data, maps, "chapter_unlock_state", small)

    def read_legend_restrictions(self, data: core.Data, gv: core.GameVersion):
        if gv < 20:
            return
        if gv >= 41:
            _skip_ints(data, 2)  # types, maps per type
        for map in self.all_maps():
            map.legend_restriction = data.read_int()

    def write_legend_restrictions(self, data: core.Data, gv: core.GameVersion):
        if gv < 20:
            return
        if gv >= 41:
            data.write_int(len(self.chapters))
            data.write_int(len(self.chapters[0].chapters) if self.chapters else 0)
        for map in self.all_maps():
            data.write_int(map.legend_restriction)

    def read_dicts(self, data: core.Data):
        self.chapter_completion_count = data.read_int_int_dict()
        self.displayed_cleared_limit_text = data.read_int_bool_dict()
        self.event_start_dates = data.read_int_int_dict()
        self.stages_reward_claimed = data.read_int_list()

    def write_dicts(self, data: core.Data):
        data.write_int_int_dict(self.chapter_completion_count)
        data.write_int_bool_dict(self.displayed_cleared_limit_text)
        data.write_int_int_dict(self.event_start_dates)
        data.write_int_list(self.stages_reward_claimed)

    def serialize(self) -> dict[str, Any]:
        return {
            "chapters": [group.serialize() for group in self.chapters],
            "chapter_completion_count": self.chapter_completion_count,
            "displayed_cleared_limit_text": self.displayed_cleared_limit_text,
            "event_start_dates": self.event_start_dates,
            "stages_reward_claimed": self.stages_reward_claimed,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> EventChapters:
        ev = EventChapters(
            [EventChapterGroup.deserialize(group) for group in data.get("chapters", [])]
        )
        ev.chapter_completion_count = core.int_keys(
            data.get("chapter_completion_count", {})
        )
        ev.displayed_cleared_limit_text = core.int_keys(
            data.get("displayed_cleared_limit_text", {})
        )
        ev.event_start_dates = core.int_keys(data.get("event_start_dates", {}))
        ev.stages_reward_claimed = data.get("stages_reward_claimed", [])
        return ev

    def __repr__(self) -> str:
        return (
            f"EventChapters({self.chapters}, {self.chapter_completion_count}, "
            f"{self.displayed_cleared_limit_text}, {self.event_start_dates}, "
            f"{self.stages_reward_claimed})"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EventChapters) and vars(self) == vars(other)

    def get_total_stars(self, type: int, map: int) -> int:
        try:
            return len(self.chapters[type].chapters[map].chapters)
        except IndexError:
            return len(self.chapters[0].chapters[0].chapters)

    def get_total_stages(self, type: int, map: int, star: int) -> int:
        try:
            return len(self.chapters[type].chapters[map].chapters[star].stages)
        except IndexError:
            return len(self.chapters[0].chapters[0].chapters[0].stages)

    @staticmethod
    def ask_stars(
        max_stars: int, prompt: str = "custom_star_count_per_chapter"
    ) -> int | None:
        if max_stars <= 1:
            return max_stars
        stars = dialog_creator.int_input_key(
            prompt,
            min=1,
            _max=dialog_creator.MaxValue.always_cap(max_stars),
            max=max_stars,
        )
        if stars is None:
            return None
        return stars

    @staticmethod
    def ask_stars_unclear(
        max_stars: int, prompt: str = "custom_star_count_per_chapter"
    ) -> int | None:
        stars = dialog_creator.int_input_key(
            prompt,
            _max=dialog_creator.MaxValue.always_cap(max_stars),
            min=0,
            max=max_stars,
        )
        if stars is None:
            return None
        return stars

    @staticmethod
    def get_stage_names(map_names: core.MapNames, chapter_id: int) -> list[str] | None:
        stage_names = map_names.stage_names.get(chapter_id)
        if stage_names is None:
            return None
        new_stage_names: list[str] = []
        for stage in stage_names:
            if stage == "＠":
                continue
            new_stage_names.append(stage)
        return new_stage_names

    @staticmethod
    def ask_stages(map_names: core.MapNames, chapter_id: int) -> list[int] | None:
        stage_names = EventChapters.get_stage_names(map_names, chapter_id)
        if stage_names is None:
            return None

        dialog_creator.display_options_key(stage_names, "select_stage")

        choices = dialog_creator.range_multi_input_key(
            "stages_select", dialog_creator.MaxValue.always_cap(len(stage_names)), 1
        )
        if choices is None:
            return None
        return [c - 1 for c in choices]

    @staticmethod
    def ask_stages_stage_names(stage_names: list[str]) -> list[int] | None:
        val = EventChapters.ask_stages_stage_names_one(stage_names)
        if val is None:
            return None
        return list(range(val + 1))

    @staticmethod
    def ask_stages_stage_names_one(stage_names: list[str]) -> int | None:
        new_stage_names: list[str] = []
        for stage in stage_names:
            if stage == "＠":
                continue
            new_stage_names.append(stage)
        stage_names = new_stage_names
        choice = dialog_creator.basic_pick_key_index(
            stage_names,
            dialog="select_stage_progress",
        )
        if choice is None:
            return None
        return choice

    @staticmethod
    def ask_clear_amount() -> int | None:
        val = dialog_creator.int_input_key(
            "clear_amount_enter",
            dialog_creator.MaxValue.i16(
                core.core_data.max_value_manager.stage_clear_count
            ),
        )

        return val

    @staticmethod
    def edit_sol_chapters(save_file: core.SaveFile):
        EventChapters.edit_chapters(save_file, 0, "N", 0)

    @staticmethod
    def edit_event_chapters(save_file: core.SaveFile):
        EventChapters.edit_chapters(save_file, 1, "S", 1000)

    @staticmethod
    def edit_collab_chapters(save_file: core.SaveFile):
        EventChapters.edit_chapters(save_file, 2, "C", 2000)

    @staticmethod
    def select_map_names(names_dict: dict[int, str | None]) -> list[int] | None:
        map_ids: list[int] = []
        names_list: list[str] = []
        names_dict = dict(sorted(names_dict.items()))
        ids = list(names_dict.keys())
        for id, map_name in names_dict.items():
            if map_name is None:
                map_name = core.core_data.local_manager.get_key(
                    "unknown_map_name", id=id
                )
            else:
                map_name = core.core_data.local_manager.get_key(
                    "map_name", name=map_name, id=id, escape=False
                )
            names_list.append(map_name)

        while True:
            dialog_creator.display_options_key(names_list, "select_map")
            if names_list:
                example_name = names_list[0]
            else:
                example_name = ""
            usr_input = (
                color.color_input_key(
                    "select_map_dialog", example=example_name, escape=False
                )
                .lower()
                .strip()
            )
            if usr_input == core.localize("quit_key"):
                return None
            if usr_input.lower() == core.localize("all").lower():
                usr_ids = list(range(1, len(names_list) + 1))
            elif usr_input.strip(" -0123456789"):
                usr_ids = None  # a name to search for
            else:
                usr_ids = dialog_creator.range_basic_parse(
                    usr_input,
                    max=dialog_creator.MaxValue.always_cap(len(names_list)),
                    min=1,
                )
            if not usr_ids:
                found_names: list[tuple[int, str]] = []
                for i, name in enumerate(names_list):
                    if usr_input.replace(" ", "_") in name.lower().strip().replace(
                        " ", "_"
                    ):
                        true_id = ids[i]
                        found_names.append((true_id, name))

                if len(found_names) == 0:
                    color.color_print_key("no_map_found", name=usr_input)
                elif len(found_names) == 1:
                    id = found_names[0][0]
                    true_id = ids[id]
                    if true_id not in map_ids:
                        map_ids.append(true_id)
                else:
                    selected_ids = dialog_creator.multi_select_indexes_key(
                        [name for _, name in found_names],
                        dialog="select_map_from_names",
                    )
                    if selected_ids is None:
                        continue
                    for i in selected_ids:
                        id = found_names[i][0]
                        true_id = ids[id]
                        if true_id not in map_ids:
                            map_ids.append(true_id)
            else:
                for id in usr_ids:
                    id -= 1
                    true_id = ids[id]
                    if true_id not in map_ids:
                        map_ids.append(true_id)

            color.color_print_key("current_maps", maps=map_ids)

            for id in map_ids:
                name = names_dict[id]
                EventChapters.print_current_chapter(name, id)

            option = dialog_creator.basic_keys_pick_key_index(
                ["keep_selecting", "remove_selection", "finish_selection"],
                dialog="map_selection_q",
            )
            if option is None:
                return None
            if option == 0:
                continue
            if option == 1:
                map_ids.clear()
            else:
                break
        return map_ids

    @staticmethod
    def print_current_chapter(name: str | None, id: int):
        if name is None:
            name = core.core_data.local_manager.get_key("unknown_map_name", id=id)
        color.color_print_key("current_sol_chapter", escape=False, name=name, id=id)

    @staticmethod
    def print_current_stage(name: str | None, index: int):
        if name is None:
            name = core.core_data.local_manager.get_key(
                "unknown_stage_name", index=index
            )
        color.color_print_key("current_stage_map", name=name, index=index)

    @staticmethod
    def edit_chapters(
        save_file: core.SaveFile, type: int, letter_code: str, base_index: int
    ):
        edits.map.edit_chapters(
            save_file,
            save_file.event_stages,
            letter_code,
            type=type,
            base_index=base_index,
        )

    def unclear_rest(
        self,
        stages: list[int],
        stars: int,
        id: int,
        type: int,
    ):
        if not stages:
            return
        for star in range(stars, self.get_total_stars(type, id)):
            for stage in range(max(stages), self.get_total_stages(type, id, star)):
                self.chapters[type].chapters[id].chapters[star].stages[
                    stage
                ].clear_times = 0
                self.chapters[type].chapters[id].chapters[star].clear_progress = 0


def _skip_ints(data: core.Data, n: int):
    for _ in range(n):
        data.read_int()


def _write_ints(data: core.Data, values: list[int]):
    for value in values:
        data.write_int(value)
