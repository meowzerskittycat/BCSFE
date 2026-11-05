from __future__ import annotations
import time
from dataclasses import dataclass
from bcsfe import core
from bcsfe.cli import dialog_creator, color
from bcsfe.core.io.schema import (
    F64,
    I8,
    I32,
    Array,
    Bool,
    Nested,
    Optional,
    Struct,
    Tuple,
    field,
)


@dataclass
class Stage(Struct):
    level: int = field(I32)
    stage_id: int = field(I32)
    decoding_satus: int = field(I8)
    start_time: float = field(F64)


@dataclass
class Enigma(Struct):
    energy_since_1: int = field(I32)
    energy_since_2: int = field(I32)
    enigma_level: int = field(I8)
    unknown_1: int = field(I8)
    unknown_2: bool = field(Bool)
    stages: list[Stage] = field(Array(Nested(Stage), I8))
    extra: tuple[int, int, int, float] | None = field(
        Optional(Tuple(I32, I32, I8, F64)), since=140500
    )

    def edit_enigma(self, save_file: core.SaveFile):
        names = core.MapNames(save_file, "H", base_index=25000).map_names
        names_list: list[str] = []
        keys = list(names.keys())
        keys.sort()
        for id in keys:
            name = names[id]
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_enigma_name", id=id
                )
            names_list.append(name)

        base_level = 25000

        color.color_print_key("current_enigma_stages")
        for stage in self.stages:
            name = names[stage.stage_id - base_level]
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_enigma_name", id=stage.stage_id
                )
            color.color_print_key(
                "enigma_stage", name=name, id=stage.stage_id - base_level
            )

        if self.stages:
            wipe = dialog_creator.yes_no_key("wipe_enigma")
            if wipe is None:
                return
            if wipe:
                for stage in self.stages:
                    id = stage.stage_id
                    save_file.event_stages.chapter_completion_count[id] = 0
                self.stages = []

        ids = dialog_creator.multi_select_indexes_key(
            names_list,
            "enigma_select",
        )
        if ids is None:
            return

        for enigma_id in ids:
            abs_id = enigma_id + base_level
            save_file.event_stages.chapter_completion_count[abs_id] = 0
            # TODO: level? they can go much higher than 3... not sure it really matters though
            stage = Stage(3, abs_id, 2, int(time.time()))
            self.stages.append(stage)

        color.color_print_key("enigma_success")


def edit_enigma(save_file: core.SaveFile):
    save_file.enigma.edit_enigma(save_file)
