from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt


def edit_base_materials(materials: core.BaseMaterials, save_file: core.SaveFile):
    names = core.core_data.get_gatya_item_names(save_file).names
    items = core.core_data.get_gatya_item_buy(save_file).get_by_category(7)
    if items is None:
        return
    if names is None:
        return
    names = [names[item.id] for item in items]
    base_materials = [base_material.amount for base_material in materials.materials]
    values = dialog_creator.edit_ints_key(
        "base_materials",
        names,
        base_materials,
        prompt.MaxValue.i32(core.core_data.max_value_manager.base_materials),
    )
    materials.materials = [
        core.game.gamoto.base_materials.Material(value) for value in values
    ]


def edit_engineers(ototo: core.Ototo, save_file: core.SaveFile):
    name = core.core_data.get_gatya_item_names(save_file).get_name(92)
    if name is None:
        name = core.localize("engineers")
    ototo.engineers = dialog_creator.edit_int_raw(
        name,
        ototo.engineers,
        prompt.MaxValue.i32(core.Ototo.get_max_engineers(save_file)),
    )


def display_current_cannons(
    ototo: core.Ototo, save_file: core.SaveFile
) -> list[str] | None:
    descriptions = core.game.gamoto.ototo.CannonDescriptions(save_file)
    recipe_unlocks = core.game.gamoto.ototo.CastleRecipeUnlock(save_file)

    color.color_print_key("current_cannon_stats")

    if ototo.cannons is None:
        ototo.cannons = core.game.gamoto.ototo.Cannons.init(save_file.game_version)

    names: list[str] = []
    longest_part_name = descriptions.get_longest_longest_part_name()
    if longest_part_name is None:
        return None
    longest_part_name = len(longest_part_name)

    for cannon_id, cannon in ototo.cannons.cannons.items():
        description = descriptions.get_cannon_description(cannon_id)
        if description is None:
            continue
        recipe_unlock = recipe_unlocks.get_recipe_unlock(cannon_id)
        if recipe_unlock is None:
            continue
        cannon_name = description.get_cannon_name()
        names.append(cannon_name)
        text = cannon_name
        if cannon_id != 0:
            cannon_name_length = len(cannon_name) - 10
            buffer = " " * (longest_part_name - cannon_name_length)
            text += core.core_data.local_manager.get_key(
                "development",
                development=core.Ototo.get_stage_name(cannon.development),
                escape=False,
                buffer=buffer,
            )

        for part_id, level in enumerate(cannon.levels):
            if part_id == 0:
                level += 1

            text += "\n"
            text += "        "
            buffer = " " * (
                longest_part_name - len(description.get_part_name(part_id)) + 2
            )
            name = description.get_part_name(part_id)
            text += core.core_data.local_manager.get_key(
                "cannon_part", name=name, level=level, buffer=buffer
            )

        text += "\n"

        color.color_print_key("cannon_stats", parts=text, escape=False)

    return names


def edit_cannons(ototo: core.Ototo, save_file: core.SaveFile):
    if ototo.cannons is None:
        ototo.cannons = core.game.gamoto.ototo.Cannons.init(save_file.game_version)

    names = display_current_cannons(ototo, save_file)
    if names is None:
        return

    cannon_ids = prompt.choose_many(names, dialog="select_cannon")
    if cannon_ids is None:
        return

    all_at_once = False

    if len(cannon_ids) > 1:
        choice = prompt.choose(
            prompt.keys(["individual", "edit_all_at_once"]),
            dialog="cannon_edit_type",
        )
        if choice is None:
            return
        if choice == 0:
            all_at_once = False
        else:
            all_at_once = True

    if len(cannon_ids) > 1 or (len(cannon_ids) == 1 and cannon_ids[0] != 0):
        choice = prompt.choose(
            prompt.keys(["development_o", "level_o"]), dialog="cannon_dev_level_q"
        )
        if choice is None:
            return
    else:
        choice = 1
    if choice == 0:
        edit_cannon_development(ototo, save_file, all_at_once, cannon_ids)
    elif choice == 1:
        edit_cannon_level(ototo, save_file, all_at_once, cannon_ids)

    color.color_print_key("cannon_success")

    display_current_cannons(ototo, save_file)


def select_development(ototo: core.Ototo) -> int | None:
    return prompt.choose(
        prompt.keys(["none", "foundation", "style", "effect"]),
        dialog="select_development",
    )


def edit_cannon_development(
    ototo: core.Ototo,
    save_file: core.SaveFile,
    all_at_once: bool,
    cannon_ids: list[int],
):
    if ototo.cannons is None:
        ototo.cannons = core.game.gamoto.ototo.Cannons.init(save_file.game_version)
    if all_at_once:
        development = select_development(ototo)
        if development is None:
            return
        for cannon_id in cannon_ids:
            if cannon_id == 0:
                continue
            ototo.cannons.cannons[cannon_id].development = development
    else:
        for cannon_id in cannon_ids:
            if cannon_id == 0:
                continue
            cannon_description = core.game.gamoto.ototo.CannonDescriptions(
                save_file
            ).get_cannon_description(cannon_id)
            if cannon_description is None:
                continue
            current_development = ototo.cannons.cannons[cannon_id].development

            color.color_print_key(
                "selected_cannon_stage",
                name=cannon_description.get_cannon_name(),
                stage=core.Ototo.get_stage_name(current_development),
                escape=False,
            )
            development = select_development(ototo)
            if development is None:
                return
            ototo.cannons.cannons[cannon_id].development = development


def edit_cannon_level(
    ototo: core.Ototo,
    save_file: core.SaveFile,
    all_at_once: bool,
    cannon_ids: list[int],
):
    if ototo.cannons is None:
        ototo.cannons = core.game.gamoto.ototo.Cannons.init(save_file.game_version)
    cannon_descriptions = core.game.gamoto.ototo.CannonDescriptions(save_file)
    cannon_recipe = core.game.gamoto.ototo.CastleRecipeUnlock(save_file)
    if all_at_once:
        max_part_level_0 = cannon_recipe.get_max_part_level(0)
        max_part_level_1 = cannon_recipe.get_max_part_level(1)
        max_part_level_2 = cannon_recipe.get_max_part_level(2)
        if (
            max_part_level_0 is None
            or max_part_level_1 is None
            or max_part_level_2 is None
        ):
            return
        levels = dialog_creator.edit_ints_key(
            "cannon_level",
            [
                core.localize("effect"),
                core.localize("improved_foundation"),
                core.localize("improved_style"),
            ],
            [0, 0, 0],
            max=dialog_creator.MultiMax.new(
                [
                    prompt.MaxValue.i32(max_part_level_0),
                    prompt.MaxValue.i32(max_part_level_1),
                    prompt.MaxValue.i32(max_part_level_2),
                ]
            ),
        )
        if not levels:
            return
        for cannon_id in cannon_ids:
            cannon = ototo.get_cannon(cannon_id)
            if cannon is None:
                continue
            cannon.development = max(cannon.development, 3)

            for part_id, level in enumerate(levels):
                if part_id == 0:
                    level -= 1
                max_level = cannon_recipe.get_max_level(cannon_id, part_id)
                if max_level is None:
                    continue
                if part_id >= len(cannon.levels):
                    break
                cannon.levels[part_id] = min(level, max_level)
    else:
        for cannon_id in cannon_ids:
            cannon = ototo.get_cannon(cannon_id)
            if cannon is None:
                continue
            cannon.development = max(cannon.development, 3)

            cannon_desc = cannon_descriptions.get_cannon_description(cannon_id)
            if cannon_desc is None:
                continue
            levels = cannon.levels
            levels[0] += 1
            names = ["effect", "improved_foundation", "improved_style"]
            if cannon_id == 0:
                names = ["effect"]
            max_part_level_0 = cannon_recipe.get_max_part_level(0)
            max_part_level_1 = cannon_recipe.get_max_part_level(1)
            max_part_level_2 = cannon_recipe.get_max_part_level(2)
            if (
                max_part_level_0 is None
                or max_part_level_1 is None
                or max_part_level_2 is None
            ):
                return

            color.color_print(cannon_desc.get_cannon_name())

            levels = dialog_creator.edit_ints_raw(
                cannon_desc.get_cannon_name(),
                [core.localize(n) for n in names],
                levels,
                max=dialog_creator.MultiMax.new(
                    [
                        prompt.MaxValue.i32(max_part_level_0),
                        prompt.MaxValue.i32(max_part_level_1),
                        prompt.MaxValue.i32(max_part_level_2),
                    ]
                ),
            )
            for part_id, level in enumerate(levels):
                if part_id == 0:
                    level -= 1
                cannon.levels[part_id] = level


def edit_cannon(save_file: core.SaveFile):
    edit_cannons(save_file.ototo, save_file)
