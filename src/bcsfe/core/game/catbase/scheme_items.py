from dataclasses import dataclass

from bcsfe import core
from bcsfe.core.io.schema import I32, Array, Struct, field


class SchemeDataItem:
    def __init__(
        self,
        id: int,
        type: int,
        type_id: int,
        item_id: int,
        number: int,
        type_id2: int | None = None,
        item_id2: int | None = None,
        number2: int | None = None,
        type_id3: int | None = None,
        item_id3: int | None = None,
        number3: int | None = None,
    ):
        self.id = id
        self.type = type
        self.type_id = type_id
        self.item_id = item_id
        self.number = number
        self.type_id2 = type_id2
        self.item_id2 = item_id2
        self.number2 = number2
        self.type_id3 = type_id3
        self.item_id3 = item_id3
        self.number3 = number3

    def is_cat(self) -> bool:
        return self.type_id == 1

    def get_name(self, localizable: core.Localizable) -> str | None:
        key = f"scheme_popup_{self.id}"
        name = localizable.get(key)
        if name is None:
            return None
        return name.replace("<flash>,", "").replace("<flash>", "")


@dataclass
class SchemeItems(Struct):
    to_obtain: list[int] = field(Array(I32))
    received: list[int] = field(Array(I32))
