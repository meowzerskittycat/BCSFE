from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import F64, I32, Bool, Map, Nested, String, Struct, field


@dataclass
class PurchasedPack(Struct):
    __transparent__: ClassVar[bool] = True
    purchased: bool = field(Bool)


@dataclass
class PurchaseSet(Struct):
    __transparent__: ClassVar[bool] = True
    purchases: dict[str, PurchasedPack] = field(Map(String, Nested(PurchasedPack)))


@dataclass
class Purchases(Struct):
    __transparent__: ClassVar[bool] = True
    purchases: dict[int, PurchaseSet] = field(Map(I32, Nested(PurchaseSet)))


@dataclass
class ItemPack(Struct):
    purchases: Purchases = field(Nested(Purchases))
    displayed_packs: dict[int, bool] = field(Map(I32, Bool), part="displayed_packs")
    three_days_started: bool = field(Bool, part="three_days")
    three_days_end_timestamp: float = field(F64, part="three_days")
