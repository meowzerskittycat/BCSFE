from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Bool, Map, Nested, Struct, field
from bcsfe import core


@dataclass
class Popup(Struct):
    __transparent__: ClassVar[bool] = True
    seen: bool = field(Bool)


@dataclass
class UnlockPopups(Struct):
    __transparent__: ClassVar[bool] = True
    popups: dict[int, Popup] = field(Map(I32, Nested(Popup)))


class UnlockPopupLine:
    def __init__(
        self,
        popup_id: int,
        enabled: bool,
        conditions: int,
        stage: int,
        map_conditions: int,
        user_rank: int,
        get_char_id1: int,
        get_char_id2: int,
        os_id: int,
        unlock_eye_1_id: int,
        add_level1: int,
        unlock_eye_2_id: int,
        add_level2: int,
        unlock_plus_id: int,
        add_level: int,
        skill_id: int,
        item_id: int,
        num: int,
        help_enabled: bool,
    ):
        self.popup_id = popup_id
        self.enabled = enabled
        self.conditions = conditions
        self.stage = stage
        self.map_conditions = map_conditions
        self.user_rank = user_rank
        self.get_char_id1 = get_char_id1
        self.get_char_id2 = get_char_id2
        self.os_id = os_id
        self.unlock_eye_1_id = unlock_eye_1_id
        self.add_level1 = add_level1
        self.unlock_eye_2_id = unlock_eye_2_id
        self.add_level2 = add_level2
        self.unlock_plus_id = unlock_plus_id
        self.add_level = add_level
        self.skill_id = skill_id
        self.item_id = item_id
        self.num = num
        self.help_enabled = help_enabled

    @staticmethod
    def from_csv_row(row: core.Row) -> UnlockPopupLine:
        return UnlockPopupLine(
            row.next_int(),
            row.next_bool(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_int(),
            row.next_bool(),
        )


class UnlockPopupData:
    def __init__(self, popups: list[UnlockPopupLine]):
        self.popups = popups

    @staticmethod
    def from_csv(csv: core.CSV) -> UnlockPopupData:
        popups: list[UnlockPopupLine] = []
        for line in csv.lines[1:]:
            popups.append(UnlockPopupLine.from_csv_row(line))

        return UnlockPopupData(popups)

    @staticmethod
    def from_save(save_file: core.SaveFile) -> UnlockPopupData | None:
        gdg = core.core_data.get_game_data_getter(save_file)
        data = gdg.download("DataLocal", "unlockPopup.tsv")
        if data is None:
            return None

        csv = core.CSV(data, "\t")

        return UnlockPopupData.from_csv(csv)
