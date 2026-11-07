from dataclasses import dataclass

from bcsfe import core
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
