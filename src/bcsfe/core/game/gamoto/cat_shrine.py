from dataclasses import dataclass
from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt
from bcsfe.core.io.schema import F64, I8, I32, I64, Array, Bool, Struct, field


@dataclass
class CatShrine(Struct):
    unknown: bool = field(Bool)
    stamp_1: float = field(F64)
    stamp_2: float = field(F64)
    shrine_gone: bool = field(Bool)
    flags: list[int] = field(Array(I8, I8))
    xp_offering: int = field(I64)
    dialogs: int = field(I32, part="dialogs")

    def appear(self):
        self.shrine_gone = False
        self.stamp_1 = 0.0
        self.stamp_2 = 0.0

    def disappear(self):
        self.shrine_gone = True

    @staticmethod
    def edit_level(save_file: core.SaveFile):
        data = core.core_data.get_cat_shrine_levels(save_file)
        max_level = data.get_max_level()
        if max_level is None:
            return
        level = prompt.number(
            "shrine_level_dialog",
            min=1,
            max=prompt.MaxValue.i32(max_level),
            max_level=max_level,
        )
        if level is None:
            return
        xp = data.get_xp_from_level(level)
        if xp is None:
            return
        save_file.cat_shrine.xp_offering = xp

    @staticmethod
    def edit_xp(save_file: core.SaveFile):
        data = core.core_data.get_cat_shrine_levels(save_file)
        max_xp = data.get_max_xp()
        if max_xp is None:
            return
        xp = prompt.number(
            "shrine_xp_dialog",
            min=0,
            max=prompt.MaxValue.i32(max_xp),
            max_xp=max_xp,
        )
        if xp is None:
            return
        save_file.cat_shrine.xp_offering = xp

    @staticmethod
    def edit_catshrine(save_file: core.SaveFile):
        shrine = save_file.cat_shrine
        xp = shrine.xp_offering
        data = core.core_data.get_cat_shrine_levels(save_file)
        level = data.get_level_from_xp(xp)
        color.color_print_key("current_shrine_xp_level", level=level, xp=xp)
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key("shrine_level", lambda _: CatShrine.edit_level(save_file))
            .add_new_key("shrine_xp", lambda _: CatShrine.edit_xp(save_file))
            .add_new_key("make_catshrine_appear", lambda _: shrine.appear())
            .add_new_key("make_catshrine_disappear", lambda _: shrine.disappear()),
            "cat_shrine_choice_dialog",
        )

        xp = shrine.xp_offering
        level = data.get_level_from_xp(xp)
        if level is None:
            return

        shrine.dialogs = level - 1

        color.color_print_key("current_shrine_xp_level", level=level, xp=xp)
        color.color_print_key("cat_shrine_edited")


class CatShrineLevels:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.boundaries = self.get_boundaries()

    def get_boundaries(self) -> list[int] | None:
        file_name = "jinja_level.csv"
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("resLocal", file_name)
        if data is None:
            return None
        csv = core.CSV(
            data,
            delimiter=core.Delimeter.from_country_code_res(self.save_file.cc),
        )
        boundaries: list[int] = []
        counter = 0
        for row in csv:
            xp = row[0].to_int()
            counter += xp
            boundaries.append(counter)

        return boundaries

    def get_level_from_xp(self, xp: int) -> int | None:
        if self.boundaries is None:
            return None
        for i, boundary in enumerate(self.boundaries):
            if xp < boundary:
                return i + 1
        return len(self.boundaries)

    def get_xp_from_level(self, level: int) -> int | None:
        if self.boundaries is None:
            return None
        if level < 1:
            return 0
        if level > len(self.boundaries):
            return self.get_max_xp()
        return self.boundaries[level - 2]

    def get_max_level(self) -> int | None:
        if self.boundaries is None:
            return None
        return len(self.boundaries)

    def get_max_xp(self) -> int | None:
        if self.boundaries is None:
            return None
        return max(self.boundaries)
