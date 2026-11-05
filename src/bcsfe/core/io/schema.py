"""Declarative binary layouts.

A save section used to need five hand-written methods that all listed the
same fields: ``init``, ``read``, ``write``, ``serialize`` and ``deserialize``.
Keeping them in step by hand is how fields end up written in a different
order than they're read, or missing from JSON exports.

With this module a section lists its fields once::

    @dataclass
    class StampData(Struct):
        current_stamp: int = field(I32)
        collected_stamp: list[int] = field(Array(I32, 30), default=lambda: [0] * 30)
        unknown: int = field(I32)
        daily_reward: int = field(I32)

and :class:`Struct` provides all five methods from that list, in field
order. Fields are read and written in declaration order, so the order of
the class body *is* the binary layout.
"""

from __future__ import annotations

import dataclasses
import struct
from collections.abc import Callable
from typing import Any, ClassVar, Generic, TypeVar

from bcsfe.core.io.data import Data

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
S = TypeVar("S", bound="Struct")


class Codec(Generic[T]):
    """How one value is laid out in the binary data and in JSON."""

    def read(self, data: Data) -> T:
        raise NotImplementedError

    def write(self, data: Data, value: T) -> None:
        raise NotImplementedError

    def default(self) -> T:
        raise NotImplementedError

    def to_json(self, value: T) -> Any:
        return value

    def from_json(self, value: Any) -> T:
        return value


class Number(Codec[int]):
    def __init__(self, fmt: str, name: str):
        self.fmt = fmt
        self.size = struct.calcsize(fmt)
        self.name = name

    def read(self, data: Data) -> int:
        return struct.unpack(data.endiness + self.fmt, data.read_bytes(self.size))[0]

    def write(self, data: Data, value: int) -> None:
        data.write_bytes(struct.pack(data.endiness + self.fmt, int(value)))

    def default(self) -> int:
        return 0

    def __repr__(self) -> str:
        return self.name


class Float(Codec[float]):
    def __init__(self, fmt: str, name: str):
        self.fmt = fmt
        self.size = struct.calcsize(fmt)
        self.name = name

    def read(self, data: Data) -> float:
        return struct.unpack(data.endiness + self.fmt, data.read_bytes(self.size))[0]

    def write(self, data: Data, value: float) -> None:
        data.write_bytes(struct.pack(data.endiness + self.fmt, float(value)))

    def default(self) -> float:
        return 0.0

    def __repr__(self) -> str:
        return self.name


class BoolCodec(Codec[bool]):
    """One byte, 0 or 1."""

    def read(self, data: Data) -> bool:
        return data.read_bool()

    def write(self, data: Data, value: bool) -> None:
        data.write_bool(bool(value))

    def default(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Bool"


class VarIntCodec(Codec[int]):
    """Big-endian base-128 integer (at most 4 bytes), as used by the game."""

    def read(self, data: Data) -> int:
        return data.read_variable_length_int()

    def write(self, data: Data, value: int) -> None:
        data.write_variable_length_int(value)

    def default(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "VarInt"


class StringCodec(Codec[str]):
    """UTF-8 string prefixed with its byte length as an int32."""

    def read(self, data: Data) -> str:
        return data.read_string()

    def write(self, data: Data, value: str) -> None:
        data.write_string(value)

    def default(self) -> str:
        return ""

    def __repr__(self) -> str:
        return "String"


I8 = Number("b", "I8")
U8 = Number("B", "U8")
I16 = Number("h", "I16")
U16 = Number("H", "U16")
I32 = Number("i", "I32")
U32 = Number("I", "U32")
I64 = Number("q", "I64")
U64 = Number("Q", "U64")
F32 = Float("f", "F32")
F64 = Float("d", "F64")
Bool = BoolCodec()
VarInt = VarIntCodec()
String = StringCodec()


class Array(Codec[list[T]]):
    """A list of `item`.

    `length` is either a fixed count (nothing is stored), or a codec for the
    count stored just before the items.
    """

    def __init__(self, item: Codec[T], length: int | Codec[int] = I32):
        self.item = item
        self.length = length

    def read(self, data: Data) -> list[T]:
        count = self.length if isinstance(self.length, int) else self.length.read(data)
        return [self.item.read(data) for _ in range(count)]

    def write(self, data: Data, value: list[T]) -> None:
        if not isinstance(self.length, int):
            self.length.write(data, len(value))
        for v in value:
            self.item.write(data, v)

    def default(self) -> list[T]:
        if isinstance(self.length, int):
            return [self.item.default() for _ in range(self.length)]
        return []

    def to_json(self, value: list[T]) -> Any:
        return [self.item.to_json(v) for v in value]

    def from_json(self, value: Any) -> list[T]:
        return [self.item.from_json(v) for v in value]

    def __repr__(self) -> str:
        return f"Array({self.item!r}, {self.length!r})"


class Map(Codec[dict[K, V]]):
    """A count (stored with `length`) followed by that many key/value pairs.

    JSON keeps keys as they come (JSON object keys become strings); the
    number codecs convert them back with int() when writing.
    """

    def __init__(self, key: Codec[K], value: Codec[V], length: Codec[int] = I32):
        self.key = key
        self.value = value
        self.length = length

    def read(self, data: Data) -> dict[K, V]:
        count = self.length.read(data)
        out: dict[K, V] = {}
        for _ in range(count):
            k = self.key.read(data)
            out[k] = self.value.read(data)
        return out

    def write(self, data: Data, value: dict[K, V]) -> None:
        self.length.write(data, len(value))
        for k, v in value.items():
            self.key.write(data, k)
            self.value.write(data, v)

    def default(self) -> dict[K, V]:
        return {}

    def to_json(self, value: dict[K, V]) -> Any:
        return {k: self.value.to_json(v) for k, v in value.items()}

    def from_json(self, value: Any) -> dict[K, V]:
        return {k: self.value.from_json(v) for k, v in value.items()}

    def __repr__(self) -> str:
        return f"Map({self.key!r}, {self.value!r}, {self.length!r})"


class Nested(Codec[S]):
    """Another :class:`Struct` embedded in place."""

    def __init__(self, struct_type: type[S]):
        self.struct_type = struct_type

    def read(self, data: Data) -> S:
        return self.struct_type.read(data)

    def write(self, data: Data, value: S) -> None:
        value.write(data)

    def default(self) -> S:
        return self.struct_type.init()

    def to_json(self, value: S) -> Any:
        return value.serialize()

    def from_json(self, value: Any) -> S:
        return self.struct_type.deserialize(value)

    def __repr__(self) -> str:
        return f"Nested({self.struct_type.__name__})"


_CODEC = "bcsfe_codec"


def field(codec: Codec[T], default: Callable[[], T] | None = None) -> Any:
    """Declare a binary field. `default` builds the value for new saves and
    for JSON that lacks the key; it defaults to the codec's default."""
    factory: Callable[[], Any] = default if default is not None else codec.default
    return dataclasses.field(default_factory=factory, metadata={_CODEC: codec})


class Struct:
    """Base class for sections whose layout is a fixed sequence of fields.

    Subclasses must be dataclasses whose fields are all declared with
    :func:`field`.
    """

    __layout__: ClassVar[list[tuple[str, Codec[Any]]] | None] = None

    @classmethod
    def layout(cls) -> list[tuple[str, Codec[Any]]]:
        cached: list[tuple[str, Codec[Any]]] | None = cls.__dict__.get("__layout__")
        if cached is None:
            layout: list[tuple[str, Codec[Any]]] = []
            for f in dataclasses.fields(cls):  # type: ignore[arg-type]
                codec: Codec[Any] | None = f.metadata.get(_CODEC)
                if codec is None:
                    raise TypeError(
                        f"{cls.__name__}.{f.name} is not declared with field()"
                    )
                layout.append((f.name, codec))
            cls.__layout__ = cached = layout
        return cached

    @classmethod
    def init(cls: type[S]) -> S:
        return cls()

    @classmethod
    def read(cls: type[S], data: Data) -> S:
        return cls(**{name: codec.read(data) for name, codec in cls.layout()})

    def write(self, data: Data) -> None:
        for name, codec in self.layout():
            codec.write(data, getattr(self, name))

    def serialize(self) -> dict[str, Any]:
        return {
            name: codec.to_json(getattr(self, name)) for name, codec in self.layout()
        }

    @classmethod
    def deserialize(cls: type[S], data: dict[str, Any]) -> S:
        values: dict[str, Any] = {}
        for f in dataclasses.fields(cls):  # type: ignore[arg-type]
            if f.name in data:
                values[f.name] = f.metadata[_CODEC].from_json(data[f.name])
        return cls(**values)
