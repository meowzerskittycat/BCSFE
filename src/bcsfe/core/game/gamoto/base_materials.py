from dataclasses import dataclass
from typing import ClassVar

from bcsfe.core.io.schema import I32, Array, Nested, Struct, field
from bcsfe import core
from bcsfe.cli import dialog_creator, prompt


@dataclass
class Material(Struct):
    __transparent__: ClassVar[bool] = True
    amount: int = field(I32)


@dataclass
class BaseMaterials(Struct):
    __transparent__: ClassVar[bool] = True
    materials: list[Material] = field(Array(Nested(Material)))

    def edit_base_materials(self, save_file: core.SaveFile):
        names = core.core_data.get_gatya_item_names(save_file).names
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(7)
        if items is None:
            return
        if names is None:
            return
        names = [names[item.id] for item in items]
        base_materials = [base_material.amount for base_material in self.materials]
        values = dialog_creator.edit_ints_key(
            "base_materials",
            names,
            base_materials,
            prompt.MaxValue.i32(core.core_data.max_value_manager.base_materials),
        )
        self.materials = [Material(value) for value in values]
