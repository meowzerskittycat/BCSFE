from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import F64, I32, Array, Map, Nested, Struct, field


@dataclass
class MapResetData(Struct):
    yearly_end_timestamp: float = field(F64)
    monthly_end_timestamp: float = field(F64)
    weekly_end_timestamp: float = field(F64)
    daily_end_timestamp: float = field(F64)


@dataclass
class MapResets(Struct):
    __transparent__: ClassVar[bool] = True
    data: dict[int, list[MapResetData]] = field(Map(I32, Array(Nested(MapResetData))))
