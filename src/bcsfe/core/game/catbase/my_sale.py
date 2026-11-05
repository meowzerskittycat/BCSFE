from __future__ import annotations

from dataclasses import dataclass

from bcsfe.core.io.data import Data
from bcsfe.core.io.schema import Bool, Map, Struct, VarInt, field


@dataclass
class MySale(Struct):
    dict_1: dict[int, int] = field(Map(VarInt, VarInt, VarInt))
    dict_2: dict[int, bool] = field(Map(VarInt, Bool, VarInt))

    @classmethod
    def read_bonus_hash(cls, stream: Data) -> MySale:
        return cls.read(stream)

    def write_bonus_hash(self, stream: Data) -> None:
        self.write(stream)
