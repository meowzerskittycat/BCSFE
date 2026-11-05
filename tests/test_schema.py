from __future__ import annotations

from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.io.schema import (
    I8,
    I16,
    I32,
    Array,
    Bool,
    Map,
    Nested,
    String,
    Struct,
    field,
)


@dataclass
class Inner(Struct):
    a: int = field(I8)
    flag: bool = field(Bool)


@dataclass
class Outer(Struct):
    count: int = field(I32)
    fixed: list[int] = field(Array(I16, 3))
    prefixed: list[int] = field(Array(I32, I8))
    lookup: dict[int, int] = field(Map(I16, I8, I16))
    name: str = field(String)
    inner: Inner = field(Nested(Inner))


def test_fields_are_written_in_declaration_order() -> None:
    value = Outer(7, [1, 2, 3], [9], {5: 6}, "ab", Inner(-1, True))
    data = core.Data()
    value.write(data)
    expected = (
        (7).to_bytes(4, "little")
        + b"\x01\x00\x02\x00\x03\x00"
        + b"\x01"
        + (9).to_bytes(4, "little")
        + b"\x01\x00"
        + b"\x05\x00\x06"
        + (2).to_bytes(4, "little")
        + b"ab"
        + b"\xff\x01"
    )
    assert data.to_bytes() == expected
    data.reset_pos()
    assert Outer.read(data) == value


def test_defaults_match_init_and_missing_json_keys() -> None:
    init = Outer.init()
    assert init.fixed == [0, 0, 0]
    assert init.prefixed == []
    assert Outer.deserialize({}) == init


def test_json_round_trip() -> None:
    value = Outer(1, [1, 2, 3], [4, 5], {1: 2}, "x", Inner(3, False))
    assert Outer.deserialize(value.serialize()) == value
    assert value.serialize()["inner"] == {"a": 3, "flag": False}
