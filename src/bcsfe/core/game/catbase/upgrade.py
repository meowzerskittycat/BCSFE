import random
from typing import Any
from bcsfe import core


class Upgrade:
    def __init__(self, plus: int, base: int):
        self.plus = plus
        self.base = base

        self.base_range: tuple[int, int] | None = None
        self.plus_range: tuple[int, int] | None = None

    def get_base(self) -> int:
        return self.base + 1

    def upgrade(self):
        self.base += 1

    def increment_base(self, amount: int):
        self.base += amount

    def increment_plus(self, amount: int):
        self.plus += amount

    def get_random_base(self, max_base: int | None = None) -> int:
        if self.base_range is None:
            return self.base
        min_b = min(self.base_range)
        max_b = max(self.base_range)
        base = random.randint(min_b, max_b)
        if max_base is not None:
            base = min(base, max_base)
        return base

    def get_random_plus(self, max_plus: int | None = None) -> int:
        if self.plus_range is None:
            return self.plus
        min_p = min(self.plus_range)
        max_p = max(self.plus_range)
        plus = random.randint(min_p, max_p)
        if max_plus is not None:
            plus = min(plus, max_plus)
        return plus

    @staticmethod
    def read(stream: core.Data) -> Upgrade:
        plus = stream.read_ushort()
        base = stream.read_ushort()

        return Upgrade(plus, base)

    def write(self, stream: core.Data):
        stream.write_ushort(self.plus)
        stream.write_ushort(self.base)

    def serialize(self) -> dict[str, Any]:
        return {
            "plus": self.plus,
            "base": self.base,
        }

    @staticmethod
    def init() -> Upgrade:
        return Upgrade(0, 0)

    def reset(self):
        self.plus = 0
        self.base = 0

    @staticmethod
    def deserialize(data: dict[str, Any]) -> Upgrade:
        return Upgrade(data.get("plus", 0), data.get("base", 0))

    def __repr__(self) -> str:
        return f"Upgrade(plus={self.plus}, base={self.base})"

    def __str__(self) -> str:
        return f"Upgrade(plus={self.plus}, base={self.base})"

    def copy(self) -> Upgrade:
        upgrade = Upgrade(self.plus, self.base)
        upgrade.base_range = self.base_range
        upgrade.plus_range = self.plus_range
        return upgrade
