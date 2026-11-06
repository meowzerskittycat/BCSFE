"""Item reward stages: whether each stage's reward has been claimed, plus the
item obtain flags stored later in the save.

`sub_chapters[map][star][stage]` is True once that reward is claimed; see
`stage_grid.read_cube` for the layout.
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from bcsfe import core
from bcsfe.core.game.map import stage_grid as grid
from bcsfe.core.io.schema import I32, Bool, Map, Nested, Struct, field


@dataclass
class ItemObtainSet(Struct):
    item_obtains: dict[int, bool] = field(Map(I32, Bool))


@dataclass
class ItemObtainSets(Struct):
    __transparent__: ClassVar[bool] = True
    item_obtain_sets: dict[int, ItemObtainSet] = field(Map(I32, Nested(ItemObtainSet)))


@dataclass
class UnobtainedItems(Struct):
    unobtained_items: dict[int, bool] = field(Map(I32, Bool))


class ItemRewardChapters:
    def __init__(self, sub_chapters: grid.Cube[bool]):
        self.sub_chapters = sub_chapters
        self.item_obtains = ItemObtainSets.init()
        self.unobtained_items = UnobtainedItems.init()

    @staticmethod
    def init(gv: core.GameVersion) -> ItemRewardChapters:
        return ItemRewardChapters(grid.new_cube(gv.game_version, False))

    @staticmethod
    def read(stream: core.Data, gv: core.GameVersion) -> ItemRewardChapters:
        return ItemRewardChapters(grid.read_cube(stream, gv.game_version, Bool))

    def write(self, stream: core.Data, gv: core.GameVersion):
        grid.write_cube(stream, gv.game_version, self.sub_chapters, Bool)

    def read_item_obtains(self, stream: core.Data):
        self.item_obtains = ItemObtainSets.read(stream)
        self.unobtained_items = UnobtainedItems.read(stream)

    def write_item_obtains(self, stream: core.Data):
        self.item_obtains.write(stream)
        self.unobtained_items.write(stream)

    def serialize(self) -> dict[str, Any]:
        return {
            "sub_chapters": self.sub_chapters,
            "item_obtains": self.item_obtains.serialize(),
            "unobtained_items": self.unobtained_items.serialize(),
        }

    @staticmethod
    def deserialize(data: dict[str, Any]) -> ItemRewardChapters:
        chapters = ItemRewardChapters(
            [
                [[bool(claimed) for claimed in star] for star in map]
                for map in data.get("sub_chapters", [])
            ]
        )
        chapters.item_obtains = ItemObtainSets.deserialize(data.get("item_obtains", {}))
        chapters.unobtained_items = UnobtainedItems.deserialize(
            data.get("unobtained_items", {})
        )
        return chapters

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ItemRewardChapters) and vars(self) == vars(other)

    def __repr__(self) -> str:
        return (
            f"ItemRewardChapters({self.sub_chapters}, {self.item_obtains}, "
            f"{self.unobtained_items})"
        )
