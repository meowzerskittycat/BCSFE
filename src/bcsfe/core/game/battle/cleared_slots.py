"""Lineups remembered for cleared stages."""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I8, I16, I32, Array, Bool, Map, Nested, Struct, field


@dataclass
class CatSlot(Struct):
    cat_id: int = field(I16)
    form: int = field(I8)


@dataclass
class LineupCat(Struct):
    index: int = field(I16)
    cats: list[CatSlot] = field(Array(Nested(CatSlot), 10))
    u1: int = field(I8)
    u2: int = field(I8)
    u3: int = field(I8)


@dataclass
class ClearedSlotsCat(Struct):
    __transparent__: ClassVar[bool] = True
    lineups: list[LineupCat] = field(Array(Nested(LineupCat), I16))


@dataclass
class StageSlot(Struct):
    __transparent__: ClassVar[bool] = True
    stage_id: int = field(I32)


@dataclass
class StageLineups(Struct):
    index: int = field(I16)
    slots: list[StageSlot] = field(Array(Nested(StageSlot), I16))


@dataclass
class ClearedStageSlots(Struct):
    lineups: list[StageLineups] = field(Array(Nested(StageLineups), I16))


@dataclass
class ClearedSlots(Struct):
    cleared_slots: ClearedSlotsCat = field(Nested(ClearedSlotsCat))
    cleared_stage_slots: ClearedStageSlots = field(Nested(ClearedStageSlots))
    unknown: dict[int, bool] = field(Map(I16, Bool, I16))
