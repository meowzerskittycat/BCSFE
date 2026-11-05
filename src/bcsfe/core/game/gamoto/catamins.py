from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Array, Nested, Struct, field


@dataclass
class Catamin(Struct):
    __transparent__: ClassVar[bool] = True
    amount: int = field(I32)


@dataclass
class Catamins(Struct):
    __transparent__: ClassVar[bool] = True
    catamins: list[Catamin] = field(Array(Nested(Catamin)))
