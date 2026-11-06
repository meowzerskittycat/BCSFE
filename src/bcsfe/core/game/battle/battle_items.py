import datetime
from dataclasses import dataclass
from math import inf
import math
from typing import Any
from bcsfe import core
from bcsfe.core.io.schema import F64, I8, Bool, Struct, field


@dataclass
class EndlessItem(Struct):
    """A battle item that is on for a while (start/end are timestamps)."""

    active: bool = field(Bool)
    unknown: bool = field(Bool)
    amount: int = field(I8)
    # new saves have always started these as int 0 (written as 0.0); kept so
    # the generated test fixtures stay identical
    start: float = field(F64, default=int)
    end: float = field(F64, default=int)

    def get_endless_duration(self) -> datetime.timedelta | None:
        if not self.active:
            return datetime.timedelta()

        if self.end == inf:
            return None
        if math.isnan(self.end) or math.isnan(self.start):
            return None

        return datetime.timedelta(
            seconds=self.end - self.start + (self.amount * 3 * 60 * 60)
        )

    def get_endless_duration_formatted(self) -> str:
        duration = self.get_endless_duration()

        if duration is None:
            return core.localize("infinity_duration")

        days = duration.days
        hours, rem = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        return core.localize(
            "duration", days=days, hours=hours, minutes=minutes, seconds=seconds
        )

    def set_duration_mins(self, mins: float, amount: int):
        self.active = True
        self.unknown = True
        self.amount = amount
        self.start = datetime.datetime.now(datetime.UTC).timestamp()
        self.end = self.start + mins * 60


class BattleItem:
    def __init__(self, amount: int):
        self.amount = amount
        self.locked = False

        self.endless_item = EndlessItem.init()

    @staticmethod
    def init() -> BattleItem:
        return BattleItem(0)

    @staticmethod
    def read_amount(stream: core.Data) -> BattleItem:
        return BattleItem(stream.read_int())

    def write_amount(self, stream: core.Data):
        stream.write_int(self.amount)

    def read_locked(self, stream: core.Data):
        self.locked = stream.read_bool()

    def write_locked(self, stream: core.Data):
        stream.write_bool(self.locked)

    def read_endless_items(self, stream: core.Data):
        self.endless_item = EndlessItem.read(stream)

    def write_endless_items(self, stream: core.Data):
        self.endless_item.write(stream)

    def serialize(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "locked": self.locked,
            "endless": self.endless_item.serialize(),
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> BattleItem:
        battle_item = BattleItem(data.get("amount", 0))
        battle_item.locked = data.get("locked", False)
        battle_item.endless_item = EndlessItem.deserialize(data.get("endless", {}))
        return battle_item

    def __repr__(self):
        try:
            return f"BattleItem({self.amount}, {self.locked}, {self.endless_item})"
        except AttributeError:
            return f"BattleItem({self.amount}, {self.endless_item})"

    def __str__(self):
        return self.__repr__()


class BattleItems:
    def __init__(self, items: list[BattleItem]):
        self.items = items
        self.lock_item = False

    @staticmethod
    def init() -> BattleItems:
        return BattleItems([BattleItem.init() for _ in range(6)])

    @staticmethod
    def read_items(stream: core.Data) -> BattleItems:
        total_items = 6
        items = [BattleItem.read_amount(stream) for _ in range(total_items)]
        return BattleItems(items)

    def write_items(self, stream: core.Data):
        for item in self.items:
            item.write_amount(stream)

    def read_locked_items(self, stream: core.Data):
        self.lock_item = stream.read_bool()
        for item in self.items:
            item.read_locked(stream)

    def write_locked_items(self, stream: core.Data):
        stream.write_bool(self.lock_item)
        for item in self.items:
            item.write_locked(stream)

    def read_endless_items(self, stream: core.Data):
        for i in range(6):
            if i >= len(self.items):
                _ = EndlessItem.read(stream)  # ensure we still read 6 items
            else:
                item = self.items[i]
                item.read_endless_items(stream)

    def write_endless_items(self, stream: core.Data):
        for i in range(6):
            if i >= len(self.items):
                EndlessItem.init().write(stream)  # ensure we still write 6 items
            else:
                item = self.items[i]
                item.write_endless_items(stream)

    def serialize(self) -> dict[str, Any]:
        return {
            "items": [item.serialize() for item in self.items],
            "lock_item": self.lock_item,
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> BattleItems:
        battle_items = BattleItems(
            [BattleItem.deserialize(item) for item in data.get("items", [])]
        )
        battle_items.lock_item = data.get("lock_item", False)
        return battle_items

    def __repr__(self):
        return f"BattleItems({self.items})"

    def __str__(self):
        return f"BattleItems({self.items})"

    def get_names(self, save_file: core.SaveFile) -> list[str] | None:
        names = core.core_data.get_gatya_item_names(save_file).names
        if names is None:
            return None
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(3)
        if items is None:
            return None

        names = [names[item.id] for item in items]
        return names
