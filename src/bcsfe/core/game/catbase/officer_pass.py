from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from bcsfe import core
from bcsfe.cli import color
from bcsfe.core.game.catbase.nyanko_club import NyankoClub
from bcsfe.core.io.schema import I16, I32, Nested, Struct, field


@dataclass
class OfficerPass(Struct):
    play_time: int = field(I32)
    gold_pass: NyankoClub = field(Nested(NyankoClub), part="gold_pass")
    cat_id: int = field(I16, part="cat_data")
    cat_form: int = field(I16, part="cat_data")

    def write(self, data: core.Data, gv: Any = None) -> None:
        # play time keeps counting in-game and can pass the int32 limit
        self.play_time = min(self.play_time, 2**31 - 1)
        super().write(data, gv)

    def reset(self, save_file: core.SaveFile):
        self.cat_id = 0
        self.cat_form = 0
        self.play_time = 0
        self.gold_pass.remove_gold_pass(save_file)

    @staticmethod
    def fix_crash(save_file: core.SaveFile):
        officer_pass = save_file.officer_pass
        officer_pass.reset(save_file)

        color.color_print_key("officer_pass_fixed")
