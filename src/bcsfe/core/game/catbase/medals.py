from __future__ import annotations
from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.io.schema import I8, I16, I32, Array, Bool, Map, Struct, field
from bcsfe.cli import color, dialog_creator


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

    @staticmethod
    def edit_medals(save_file: core.SaveFile):
        medals = save_file.medals
        medal_names = core.core_data.get_medal_names(save_file)
        if medal_names.medal_names is None:
            return
        options = ["add_medals", "remove_medals"]
        choice = dialog_creator.basic_keys_pick_key_index(
            options, dialog="medal_add_remove_dialog"
        )
        if choice is None:
            return
        add_medals = choice == 0

        medals_to_choose_from: list[tuple[int, str]] = []
        for i, medal in enumerate(medal_names.medal_names):
            if len(medal) == 0:
                continue
            if medals.has_medal(i) == add_medals:
                continue
            key = "medal_string"
            string = core.core_data.local_manager.get_key(
                key, medal_name=medal[0], medal_req=medal[1]
            )
            medals_to_choose_from.append((i, string))
        if len(medals_to_choose_from) == 0:
            return
        options = [medal[1] for medal in medals_to_choose_from]
        choices = dialog_creator.multi_select_indexes_key(
            options, dialog="select_medals"
        )
        if choices is None:
            return
        for choice in choices:
            medal_id = medals_to_choose_from[choice][0]
            if add_medals:
                medals.add_medal(medal_id)
            else:
                medals.remove_medal(medal_id)

        if add_medals:
            color.color_print_key("medals_added")
        else:
            color.color_print_key("medals_removed")

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

    def get_medal_name(self, medal_id: int) -> list[str] | None:
        if self.medal_names is None:
            return None
        if medal_id < 0 or medal_id >= len(self.medal_names):
            return []
        return self.medal_names[medal_id]
