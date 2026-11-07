from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.io.schema import I8, I16, I32, Array, Bool, Map, Struct, field


@dataclass
class Medals(Struct):
    u1: int = field(I32)
    u2: int = field(I32)
    u3: int = field(I32)
    medal_data_1: list[int] = field(Array(I16, I16))
    medal_data_2: dict[int, int] = field(Map(I16, I8, I16))
    ub: bool = field(Bool)

    def has_medal(self, medal_id: int) -> bool:
        return medal_id in self.medal_data_1

    def add_medal(self, medal_id: int) -> None:
        if self.has_medal(medal_id):
            return
        self.medal_data_1.append(medal_id)
        self.medal_data_2[medal_id] = 0

    def remove_medal(self, medal_id: int) -> None:
        if medal_id in self.medal_data_2:
            del self.medal_data_2[medal_id]
        if medal_id in self.medal_data_1:
            self.medal_data_1.remove(medal_id)


class MedalNames:
    def __init__(self, save_file: core.SaveFile):
        self.save_file = save_file
        self.medal_names = self.get_medal_names()

    def get_medal_names(self) -> list[list[str]] | None:
        file_name = "medalname.tsv"
        gdg = core.core_data.get_game_data_getter(self.save_file)
        data = gdg.download("resLocal", file_name)
        if data is None:
            return None
        csv = core.CSV(data, delimiter="\t")
        names: list[list[str]] = []
        for row in csv:
            names.append(row.to_str_list())
        return names
