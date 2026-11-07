from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Bool, Map, Nested, Struct, field


@dataclass
class Popup(Struct):
    __transparent__: ClassVar[bool] = True
    seen: bool = field(Bool)


@dataclass
class UnlockPopups(Struct):
    __transparent__: ClassVar[bool] = True
    popups: dict[int, Popup] = field(Map(I32, Nested(Popup)))
