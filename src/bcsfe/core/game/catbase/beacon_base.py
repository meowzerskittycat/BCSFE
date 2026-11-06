from dataclasses import dataclass

from bcsfe.core.io.schema import I32, Array, Bool, Map, String, Struct, field


@dataclass
class BeaconEventListScene(Struct):
    int_array: dict[int, int] = field(Map(I32, I32))
    str_array: dict[int, list[str]] = field(Map(I32, Array(String)))
    bool_array: dict[int, bool] = field(Map(I32, Bool))
