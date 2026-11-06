from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt


def edit_raw_xp(
    gamatoto: core.Gamatoto, gamatoto_levels: core.game.gamoto.gamatoto.GamatotoLevels
):
    xp = dialog_creator.edit_int_key(
        "gamatoto_xp", gamatoto.xp, prompt.MaxValue.i32().hide_max()
    )
    current_level = gamatoto_levels.get_level_from_xp(xp)

    return xp, current_level


def edit_level(
    gamatoto: core.Gamatoto,
    current_level: core.game.gamoto.gamatoto.GamatotoLevel,
    gamatoto_levels: core.game.gamoto.gamatoto.GamatotoLevels,
):
    max_v = gamatoto_levels.get_max_level()
    value = dialog_creator.edit_int_key(
        "gamatoto_level",
        current_level.level,
        (
            prompt.MaxValue.i32(max_v)
            if max_v is not None
            else prompt.MaxValue.i32().hide_max()
        ),
    )
    xp = gamatoto_levels.get_xp_from_level(value)
    return xp, gamatoto_levels.get_level(value)


def edit_gamatoto_xp(gamatoto: core.Gamatoto, save_file: core.SaveFile):
    gamatoto_levels = core.core_data.get_gamatoto_levels(save_file)
    current_level = gamatoto_levels.get_level_from_xp(gamatoto.xp)
    if current_level is None:
        return
    xp = gamatoto.xp

    color.color_print_key("gamatoto_level_current", level=current_level.level, xp=xp)
    res = dialog_creator.single_select_key(
        dialog_creator.Actions[
            tuple[int | None, core.game.gamoto.gamatoto.GamatotoLevel | None]
        ]
        .new()
        .add_new_key(
            "enter_raw_gamatoto_xp", lambda _: edit_raw_xp(gamatoto, gamatoto_levels)
        )
        .add_new_key(
            "enter_gamatoto_level",
            lambda _: edit_level(gamatoto, current_level, gamatoto_levels),  # type: ignore
        ),
        "edit_gamatoto_level_q",
    )
    if res is None:
        return
    xp, current_level = res

    if xp is None:
        return

    gamatoto.xp = xp

    if current_level is None:
        return

    color.color_print_key("gamatoto_level_success", level=current_level.level, xp=xp)


def edit_gamatoto_helpers(gamatoto: core.Gamatoto, save_file: core.SaveFile):
    members_name = core.core_data.get_gamatoto_members_name(save_file)

    gamatoto_levels = core.core_data.get_gamatoto_levels(save_file)
    max_helpers = gamatoto_levels.get_total_helpers()

    members = members_name.get_members_from_helpers(gamatoto.helpers)
    color.color_print_key("current_gamatoto_helpers")
    for member in members:
        if member is None:
            continue
        color.color_print_key(
            "gamatoto_helper",
            name=member.name,
            rarity_name=member.rarity_name,
        )
    rarity_names = members_name.get_all_rarity_names()
    if rarity_names is None:
        return

    total_rarity_amounts: list[int] = [0] * len(rarity_names)
    for helper in gamatoto.helpers.helpers:
        if not helper.is_valid():
            continue
        member = members_name.get_member(helper.id)
        if member is None:
            continue
        total_rarity_amounts[member.rarity] += 1

    rarity_amounts = dialog_creator.edit_ints_key(
        "gamatoto_helpers",
        rarity_names,
        total_rarity_amounts,
        dialog_creator.CumulativeMax.new(
            prompt.MaxValue.i32(max_helpers)
            if max_helpers is not None
            else prompt.MaxValue.i32().hide_max()
        ),
    )

    helpers: list[core.game.gamoto.gamatoto.Helper] = []
    for i, rarity_amount in enumerate(rarity_amounts):
        rarity_members = members_name.get_all_rarity(i)
        if rarity_members is None:
            continue
        for i in range(rarity_amount):
            index = i % len(rarity_members)
            member = rarity_members[index]

            helpers.append(core.game.gamoto.gamatoto.Helper(member.member_id))
    gamatoto.helpers = core.game.gamoto.gamatoto.Helpers(helpers)

    members = members_name.get_members_from_helpers(gamatoto.helpers)
    color.color_print_key("new_gamatoto_helpers")
    for member in members:
        if member is None:
            continue
        color.color_print_key(
            "gamatoto_helper",
            name=member.name,
            rarity_name=member.rarity_name,
        )


def edit_xp(save_file: core.SaveFile):
    edit_gamatoto_xp(save_file.gamatoto, save_file)


def edit_helpers(save_file: core.SaveFile):
    edit_gamatoto_helpers(save_file.gamatoto, save_file)
