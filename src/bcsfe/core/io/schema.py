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

    def read(self, data: Data, gv: Any = None) -> T:
        raise NotImplementedError

    def write(self, data: Data, value: T, gv: Any = None) -> None:
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

    def read(self, data: Data, gv: Any = None) -> int:
        return struct.unpack(data.endiness + self.fmt, data.read_bytes(self.size))[0]

    def write(self, data: Data, value: int, gv: Any = None) -> None:
        data.write_bytes(struct.pack(data.endiness + self.fmt, int(value)))

    def default(self) -> int:
        return 0

    def from_json(self, value: Any) -> int:
        return int(value)

    def __repr__(self) -> str:
        return self.name


class Float(Codec[float]):
    def __init__(self, fmt: str, name: str):
        self.fmt = fmt
        self.size = struct.calcsize(fmt)
        self.name = name

    def read(self, data: Data, gv: Any = None) -> float:
        return struct.unpack(data.endiness + self.fmt, data.read_bytes(self.size))[0]

    def write(self, data: Data, value: float, gv: Any = None) -> None:
        data.write_bytes(struct.pack(data.endiness + self.fmt, float(value)))

    def default(self) -> float:
        return 0.0

    def from_json(self, value: Any) -> float:
        return float(value)

    def __repr__(self) -> str:
        return self.name


class BoolCodec(Codec[bool]):
    """One byte, 0 or 1."""

    def read(self, data: Data, gv: Any = None) -> bool:
        return data.read_bool()

    def write(self, data: Data, value: bool, gv: Any = None) -> None:
        data.write_bool(bool(value))

    def default(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Bool"


class VarIntCodec(Codec[int]):
    """Big-endian base-128 integer (at most 4 bytes), as used by the game."""

    def read(self, data: Data, gv: Any = None) -> int:
        return data.read_variable_length_int()

    def write(self, data: Data, value: int, gv: Any = None) -> None:
        data.write_variable_length_int(value)

    def default(self) -> int:
        return 0

    def from_json(self, value: Any) -> int:
        return int(value)

    def __repr__(self) -> str:
        return "VarInt"


class StringCodec(Codec[str]):
    """UTF-8 string prefixed with its byte length as an int32."""

    def read(self, data: Data, gv: Any = None) -> str:
        return data.read_string()

    def write(self, data: Data, value: str, gv: Any = None) -> None:
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

    def read(self, data: Data, gv: Any = None) -> list[T]:
        count = (
            self.length if isinstance(self.length, int) else self.length.read(data, gv)
        )
        return [self.item.read(data, gv) for _ in range(count)]

    def write(self, data: Data, value: list[T], gv: Any = None) -> None:
        if not isinstance(self.length, int):
            self.length.write(data, len(value), gv)
        for v in value:
            self.item.write(data, v, gv)

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

    JSON object keys are always strings, so keys are converted back with
    the key codec when loading JSON.
    """

    def __init__(self, key: Codec[K], value: Codec[V], length: Codec[int] = I32):
        self.key = key
        self.value = value
        self.length = length

    def read(self, data: Data, gv: Any = None) -> dict[K, V]:
        count = self.length.read(data, gv)
        out: dict[K, V] = {}
        for _ in range(count):
            k = self.key.read(data, gv)
            out[k] = self.value.read(data, gv)
        return out

    def write(self, data: Data, value: dict[K, V], gv: Any = None) -> None:
        self.length.write(data, len(value), gv)
        for k, v in value.items():
            self.key.write(data, k, gv)
            self.value.write(data, v, gv)

    def default(self) -> dict[K, V]:
        return {}

    def to_json(self, value: dict[K, V]) -> Any:
        return {k: self.value.to_json(v) for k, v in value.items()}

    def from_json(self, value: Any) -> dict[K, V]:
        return {
            self.key.from_json(k): self.value.from_json(v) for k, v in value.items()
        }

    def __repr__(self) -> str:
        return f"Map({self.key!r}, {self.value!r}, {self.length!r})"


class Nested(Codec[S]):
    """Another :class:`Struct` embedded in place."""

    def __init__(self, struct_type: type[S]):
        self.struct_type = struct_type

    def read(self, data: Data, gv: Any = None) -> S:
        return self.struct_type.read(data, gv)

    def write(self, data: Data, value: S, gv: Any = None) -> None:
        value.write(data, gv)

    def default(self) -> S:
        return self.struct_type.init()

    def to_json(self, value: S) -> Any:
        return value.serialize()

    def from_json(self, value: Any) -> S:
        return self.struct_type.deserialize(value)

    def __repr__(self) -> str:
        return f"Nested({self.struct_type.__name__})"


class Grid(Codec[list[list[T]]]):
    """Rows of equal length: the row count, the column count, then the items
    row by row. An empty grid is written with 0 columns."""

    def __init__(self, item: Codec[T], length: Codec[int] = I32):
        self.item = item
        self.length = length

    def read(self, data: Data, gv: Any = None) -> list[list[T]]:
        rows = self.length.read(data, gv)
        cols = self.length.read(data, gv)
        return [[self.item.read(data, gv) for _ in range(cols)] for _ in range(rows)]

    def write(self, data: Data, value: list[list[T]], gv: Any = None) -> None:
        self.length.write(data, len(value), gv)
        self.length.write(data, len(value[0]) if value else 0, gv)
        for row in value:
            for v in row:
                self.item.write(data, v, gv)

    def default(self) -> list[list[T]]:
        return []

    def to_json(self, value: list[list[T]]) -> Any:
        return [[self.item.to_json(v) for v in row] for row in value]

    def from_json(self, value: Any) -> list[list[T]]:
        return [[self.item.from_json(v) for v in row] for row in value]

    def __repr__(self) -> str:
        return f"Grid({self.item!r}, {self.length!r})"


class Section(Codec[Any]):
    """A section class with its own read/write/serialize/deserialize/init,
    for embedding sections that aren't declared with the schema yet.

    `versioned` says whether its read/write (and init) take the game version.
    """

    def __init__(self, section_type: Any, versioned: bool = False):
        self.section_type = section_type
        self.versioned = versioned

    def read(self, data: Data, gv: Any = None) -> Any:
        if self.versioned:
            return self.section_type.read(data, gv)
        return self.section_type.read(data)

    def write(self, data: Data, value: Any, gv: Any = None) -> None:
        if self.versioned:
            value.write(data, gv)
        else:
            value.write(data)

    def default(self) -> Any:
        return self.section_type.init()

    def to_json(self, value: Any) -> Any:
        return value.serialize()

    def from_json(self, value: Any) -> Any:
        return self.section_type.deserialize(value)

    def __repr__(self) -> str:
        return f"Section({self.section_type.__name__})"


_CODEC = "bcsfe_codec"
_SINCE = "bcsfe_since"
_BEFORE = "bcsfe_before"
_PART = "bcsfe_part"
_TRANSIENT = "bcsfe_transient"


def field(
    codec: Codec[T],
    default: Callable[[], T] | None = None,
    *,
    since: int | None = None,
    before: int | None = None,
    part: str | None = None,
) -> Any:
    """Declare a binary field.

    `default` builds the value for new saves, for JSON that lacks the key and
    for game versions where the field isn't stored; it defaults to the
    codec's default. With `since` / `before` the field is only read and
    written when ``since <= game version < before``.

    Some sections are stored in several places in the save. Fields with a
    `part` name aren't handled by :meth:`Struct.read` / :meth:`Struct.write`;
    read and write them where they occur with :meth:`Struct.read_part` /
    :meth:`Struct.write_part`. JSON still has all fields together.
    """
    factory: Callable[[], Any] = default if default is not None else codec.default
    return dataclasses.field(
        default_factory=factory,
        metadata={_CODEC: codec, _SINCE: since, _BEFORE: before, _PART: part},
    )


def transient(default: Callable[[], T]) -> Any:
    """An attribute that is neither in the save nor in JSON (editor state)."""
    return dataclasses.field(
        default_factory=default, compare=False, repr=False, metadata={_TRANSIENT: True}
    )


class _Field:
    __slots__ = ("name", "codec", "since", "before", "part")

    def __init__(self, f: dataclasses.Field[Any]):
        self.name = f.name
        self.codec: Codec[Any] = f.metadata[_CODEC]
        self.since: int | None = f.metadata.get(_SINCE)
        self.before: int | None = f.metadata.get(_BEFORE)
        self.part: str | None = f.metadata.get(_PART)

    def present(self, gv: Any, owner: str) -> bool:
        if self.since is None and self.before is None:
            return True
        if gv is None:
            raise TypeError(f"{owner}.{self.name} depends on the game version")
        if self.since is not None and gv < self.since:
            return False
        return not (self.before is not None and gv >= self.before)


class Struct:
    """Base class for sections whose layout is a fixed sequence of fields.

    Subclasses must be dataclasses whose fields are all declared with
    :func:`field` (or :func:`transient`). Set ``__transparent__ = True`` on a
    single-field struct to make its JSON form just that field's value (e.g. a
    bare int) rather than an object.
    """

    __layout__: ClassVar[list[_Field] | None] = None
    __transparent__: ClassVar[bool] = False

    @classmethod
    def layout(cls) -> list[_Field]:
        cached: list[_Field] | None = cls.__dict__.get("__layout__")
        if cached is None:
            layout: list[_Field] = []
            for f in dataclasses.fields(cls):  # type: ignore[arg-type]
                if f.metadata.get(_TRANSIENT):
                    continue
                if f.metadata.get(_CODEC) is None:
                    raise TypeError(
                        f"{cls.__name__}.{f.name} is not declared with field()"
                    )
                layout.append(_Field(f))
            if cls.__transparent__ and len(layout) != 1:
                raise TypeError(f"transparent {cls.__name__} must have one field")
            cls.__layout__ = cached = layout
        return cached

    @classmethod
    def _part(cls, part: str | None) -> list[_Field]:
        fields = [f for f in cls.layout() if f.part == part]
        if part is not None and not fields:
            raise ValueError(f"{cls.__name__} has no part {part!r}")
        return fields

    @classmethod
    def init(cls: type[S]) -> S:
        return cls()

    @classmethod
    def read(cls: type[S], data: Data, gv: Any = None) -> S:
        values: dict[str, Any] = {}
        for f in cls._part(None):
            if f.present(gv, cls.__name__):
                values[f.name] = f.codec.read(data, gv)
        return cls(**values)

    def write(self, data: Data, gv: Any = None) -> None:
        self.write_part(data, None, gv)

    def read_part(self, data: Data, part: str, gv: Any = None) -> None:
        for f in self._part(part):
            if f.present(gv, type(self).__name__):
                setattr(self, f.name, f.codec.read(data, gv))

    def write_part(self, data: Data, part: str | None, gv: Any = None) -> None:
        for f in self._part(part):
            if f.present(gv, type(self).__name__):
                f.codec.write(data, getattr(self, f.name), gv)

    def serialize(self) -> Any:
        layout = self.layout()
        if self.__transparent__:
            f = layout[0]
            return f.codec.to_json(getattr(self, f.name))
        return {f.name: f.codec.to_json(getattr(self, f.name)) for f in layout}

    @classmethod
    def deserialize(cls: type[S], data: Any) -> S:
        layout = cls.layout()
        if cls.__transparent__:
            f = layout[0]
            return cls(**{f.name: f.codec.from_json(data)})
        values: dict[str, Any] = {}
        for f in layout:
            if f.name in data:
                values[f.name] = f.codec.from_json(data[f.name])
        return cls(**values)
