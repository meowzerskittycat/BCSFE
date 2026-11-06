from dataclasses import dataclass
from typing import ClassVar

from bcsfe import core
from bcsfe.core.io.schema import F64, I32, Array, Bool, Map, Nested, Struct, field


@dataclass
class MemberName:
    member_id: int
    rarity: int
    bonus: int
    name: str
    rarity_name: str
    description: list[str]


class GamatotoMembersName:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.members = self.read_members()

    def read_members(self) -> list[MemberName] | None:
        members: list[MemberName] = []
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download(
            "resLocal",
            f"GamatotoExpedition_Members_name_{core.core_data.get_lang(self.save_file)}.csv",
        )
        if data is None:
            return None
        csv = core.CSV(
            data,
            delimiter=core.Delimeter.from_country_code_res(self.save_file.cc),
            remove_empty=False,
        )
        for line in csv.lines[1:]:
            if line[0].to_int() == -1:
                continue
            members.append(
                MemberName(
                    line[0].to_int(),
                    line[1].to_int(),
                    line[2].to_int(),
                    line[3].to_str(),
                    line[4].to_str(),
                    line[5:].to_str_list(),
                )
            )
        return members

    def get_member(self, member_id: int) -> MemberName | None:
        if self.members is None:
            return None
        for member in self.members:
            if member.member_id == member_id:
                return member
        return None

    def get_members_from_ids(self, ids: list[int]) -> list[MemberName | None]:
        return [self.get_member(id) for id in ids]

    def get_all_rarity(self, rarity: int) -> list[MemberName] | None:
        if self.members is None:
            return None

        return [member for member in self.members if member.rarity == rarity]

    def get_members_from_helpers(self, helpers: Helpers) -> list[MemberName | None]:
        return self.get_members_from_ids(
            [helper.id for helper in helpers.helpers if helper.is_valid()]
        )

    def get_all_rarity_names(self) -> list[str] | None:
        if self.members is None:
            return None
        names: dict[int, str] = {}
        for member in self.members:
            names[member.rarity] = member.rarity_name
        return [names[i] for i in range(len(names))]


@dataclass
class GamatotoLevel:
    level: int
    xp_needed: int
    discovery_bonus: int
    skin: int


@dataclass
class GamatotoLimit:
    max_level: int
    total_stages: int
    total_helpers: int


class GamatotoLevels:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.levels = self.read_levels()
        self.limit = self.read_max_level()

    def read_levels(self) -> list[GamatotoLevel] | None:
        levels: list[GamatotoLevel] = []
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("DataLocal", "GamatotoExpedition.csv")
        if data is None:
            return None
        csv = core.CSV(data)
        for i, line in enumerate(csv):
            levels.append(
                GamatotoLevel(
                    i + 1, line[0].to_int(), line[1].to_int(), line[2].to_int()
                )
            )
        return levels

    def read_max_level(self) -> GamatotoLimit | None:
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("DataLocal", "GamatotoExpedition_Limit.csv")
        if data is None:
            return None
        csv = core.CSV(data)
        line = csv[0]
        return GamatotoLimit(line[0].to_int(), line[1].to_int(), line[2].to_int())

    def get_level(self, level: int) -> GamatotoLevel | None:
        if self.levels is None:
            return None
        if level < 1:
            return None
        return self.levels[level - 1]

    def get_all_levels(self) -> list[GamatotoLevel] | None:
        return self.levels

    def get_level_from_xp(self, xp: int) -> GamatotoLevel | None:
        if self.levels is None or self.limit is None:
            return None
        for level in self.levels:
            if level.level >= self.limit.max_level:
                break
            if level.xp_needed == -1:
                continue
            if xp < level.xp_needed:
                return level
        if self.limit.max_level >= len(self.levels):
            return self.levels[-1]
        return self.levels[self.limit.max_level - 1]

    def get_xp_from_level(self, level: int) -> int | None:
        if self.levels is None:
            return None
        level -= 1
        if level < 1:
            return 0
        return self.levels[level - 1].xp_needed

    def get_max_level(self) -> int | None:
        if self.limit is None:
            return None
        return self.limit.max_level

    def get_total_stages(self) -> int | None:
        if self.limit is None:
            return None
        return self.limit.total_stages

    def get_total_helpers(self) -> int | None:
        if self.limit is None:
            return None
        return self.limit.total_helpers


@dataclass
class Helper(Struct):
    __transparent__: ClassVar[bool] = True
    id: int = field(I32, default=lambda: -1)

    def is_valid(self) -> bool:
        return self.id != -1


@dataclass
class Helpers(Struct):
    __transparent__: ClassVar[bool] = True
    helpers: list[Helper] = field(Array(Nested(Helper)))


@dataclass
class Gamatoto(Struct):
    remaining_seconds: float = field(F64)
    return_flag: bool = field(Bool)
    xp: int = field(I32)
    dest_id: int = field(I32)
    recon_length: int = field(I32)
    unknown: int = field(I32)
    notif_value: int = field(I32)
    helpers: Helpers = field(Nested(Helpers), part="helpers")
    is_ad_present: bool = field(Bool, part="helpers")
    skin: int = field(I32, part="skin")
    collab_flags: dict[int, bool] = field(Map(I32, Bool), part="collab")
    collab_durations: dict[int, float] = field(Map(I32, F64), part="collab")
