from __future__ import annotations

import json
from dataclasses import dataclass
from typing import ClassVar

import pytest

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


@dataclass
class Versioned(Struct):
    always: int = field(I8)
    new: int = field(I8, default=lambda: 7, since=100)
    old: int = field(I8, before=100)


def test_version_gated_fields() -> None:
    data = core.Data()
    Versioned(1, 2, 3).write(data, 100)
    assert data.to_bytes() == b"\x01\x02"
    data.reset_pos()
    assert Versioned.read(data, 100) == Versioned(1, 2, 0)

    data = core.Data()
    Versioned(1, 2, 3).write(data, 99)
    assert data.to_bytes() == b"\x01\x03"
    data.reset_pos()
    assert Versioned.read(data, 99) == Versioned(1, 7, 3)


def test_version_gated_fields_need_a_version() -> None:
    with pytest.raises(TypeError):
        Versioned().write(core.Data())


@dataclass
class Amount(Struct):
    __transparent__: ClassVar[bool] = True
    amount: int = field(I32)


@dataclass
class Holder(Struct):
    amounts: dict[int, Amount] = field(Map(I32, Nested(Amount)))


def test_transparent_struct_json_is_its_value() -> None:
    value = Holder({3: Amount(5)})
    assert value.serialize() == {"amounts": {3: 5}}
    # through real JSON, where keys become strings
    again = Holder.deserialize(json.loads(json.dumps(value.serialize())))
    assert again == value
