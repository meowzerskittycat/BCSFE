from dataclasses import dataclass

from bcsfe.core.io.schema import I32, Array, Struct, field


@dataclass
class StampData(Struct):
    current_stamp: int = field(I32)
    collected_stamp: list[int] = field(Array(I32, 30))
    unknown: int = field(I32)
    daily_reward: int = field(I32)
