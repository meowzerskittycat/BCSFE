from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt


def edit_level(save_file: core.SaveFile):
    data = core.core_data.get_cat_shrine_levels(save_file)
    max_level = data.get_max_level()
    if max_level is None:
        return
    level = prompt.number(
        "shrine_level_dialog",
        min=1,
        max=prompt.MaxValue.i32(max_level),
        max_level=max_level,
    )
    if level is None:
        return
    xp = data.get_xp_from_level(level)
    if xp is None:
        return
    save_file.cat_shrine.xp_offering = xp


def edit_xp(save_file: core.SaveFile):
    data = core.core_data.get_cat_shrine_levels(save_file)
    max_xp = data.get_max_xp()
    if max_xp is None:
        return
    xp = prompt.number(
        "shrine_xp_dialog",
        min=0,
        max=prompt.MaxValue.i32(max_xp),
        max_xp=max_xp,
    )
    if xp is None:
        return
    save_file.cat_shrine.xp_offering = xp


def edit_catshrine(save_file: core.SaveFile):
    shrine = save_file.cat_shrine
    xp = shrine.xp_offering
    data = core.core_data.get_cat_shrine_levels(save_file)
    level = data.get_level_from_xp(xp)
    color.color_print_key("current_shrine_xp_level", level=level, xp=xp)
    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key("shrine_level", lambda _: edit_level(save_file))
        .add_new_key("shrine_xp", lambda _: edit_xp(save_file))
        .add_new_key("make_catshrine_appear", lambda _: shrine.appear())
        .add_new_key("make_catshrine_disappear", lambda _: shrine.disappear()),
        "cat_shrine_choice_dialog",
    )

    xp = shrine.xp_offering
    level = data.get_level_from_xp(xp)
    if level is None:
        return

    shrine.dialogs = level - 1

    color.color_print_key("current_shrine_xp_level", level=level, xp=xp)
    color.color_print_key("cat_shrine_edited")
