"""EX stage clear counts: a list of chapters, each with 12 stages."""

from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Array, Nested, Struct, field


@dataclass
class Stage(Struct):
    __transparent__: ClassVar[bool] = True
    clear_amount: int = field(I32)


@dataclass
class Chapter(Struct):
    __transparent__: ClassVar[bool] = True
    stages: list[Stage] = field(Array(Nested(Stage), 12))


@dataclass
class ExChapters(Struct):
    __transparent__: ClassVar[bool] = True
    chapters: list[Chapter] = field(Array(Nested(Chapter)))
