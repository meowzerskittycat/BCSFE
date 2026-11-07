from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Array, Nested, Struct, field


@dataclass
class Material(Struct):
    __transparent__: ClassVar[bool] = True
    amount: int = field(I32)


@dataclass
class BaseMaterials(Struct):
    __transparent__: ClassVar[bool] = True
    materials: list[Material] = field(Array(Nested(Material)))
