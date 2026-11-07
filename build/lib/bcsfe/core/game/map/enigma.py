from dataclasses import dataclass
from bcsfe.core.io.schema import (
    F64,
    I8,
    I32,
    Array,
    Bool,
    Nested,
    Optional,
    Struct,
    Tuple,
    field,
)


@dataclass
class Stage(Struct):
    level: int = field(I32)
    stage_id: int = field(I32)
    decoding_satus: int = field(I8)
    start_time: float = field(F64)


@dataclass
class Enigma(Struct):
    energy_since_1: int = field(I32)
    energy_since_2: int = field(I32)
    enigma_level: int = field(I8)
    unknown_1: int = field(I8)
    unknown_2: bool = field(Bool)
    stages: list[Stage] = field(Array(Nested(Stage), I8))
    extra: tuple[int, int, int, float] | None = field(
        Optional(Tuple(I32, I32, I8, F64)), since=140500
    )
