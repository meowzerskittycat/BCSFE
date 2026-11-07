import random
from math import inf

from bcsfe import core
from bcsfe.cli import color, dialog_creator, edits, prompt
from bcsfe.core.game.catbase.gatya_item import GatyaItemCategory


class BasicItems:
    @staticmethod
    def get_name(name: str | None, key: str) -> str:
        if name is None:
            return core.core_data.local_manager.get_key(key)
        return name.strip()

    @staticmethod
    def reset_golden_cat_cpus(save_file: core.SaveFile):
        save_file.golden_cpu_count = 0

        color.color_print_key("reset_golden_cat_cpus_success")

    @staticmethod
    def edit_catfood(save_file: core.SaveFile):
        should_exit = not prompt.confirm("catfood_warning")
        if should_exit:
            return

        name = core.core_data.get_gatya_item_names(save_file).get_name(22)
        original_amount = save_file.catfood
        save_file.catfood = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "catfood"),
            save_file.catfood,
            prompt.MaxValue.i32(core.core_data.max_value_manager.catfood),
        )
        change = save_file.catfood - original_amount
        core.BackupMetaData(save_file).add_managed_item(
            core.ManagedItem.from_change(change, core.ManagedItemType.CATFOOD)
        )

    @staticmethod
    def edit_xp(save_file: core.SaveFile):
        name = core.core_data.get_gatya_item_names(save_file).get_name(6)
        save_file.xp = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "xp"),
            save_file.xp,
            prompt.MaxValue.i32(core.core_data.max_value_manager.xp),
        )

    @staticmethod
    def edit_normal_tickets(save_file: core.SaveFile):
        name = core.core_data.get_gatya_item_names(save_file).get_name(20)
        save_file.normal_tickets = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "normal_tickets"),
            save_file.normal_tickets,
            prompt.MaxValue.i32(core.core_data.max_value_manager.normal_tickets),
        )

    @staticmethod
    def edit_100_million_ticket(save_file: core.SaveFile):
        color.color_print_key("100_million_warn")
        name = core.core_data.get_gatya_item_names(save_file).get_name(212)
        save_file.hundred_million_ticket = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "100_million_tickets"),
            save_file.hundred_million_ticket,
            prompt.MaxValue.i32(
                core.core_data.max_value_manager.hundred_million_tickets
            ),
        )

    @staticmethod
    def should_go_safer_feature(
        feature_name: str, safe_feature_name: str
    ) -> bool | None:
        feature_name = core.core_data.local_manager.get_key(feature_name)
        safe_feature_name = core.core_data.local_manager.get_key(safe_feature_name)

        return dialog_creator.single_select_key(
            dialog_creator.Actions[bool | None]
            .new()
            .add_new_key("continue_editing", lambda _: False, feature_name=feature_name)
            .add_new_key(
                "go_to_safe_feature",
                lambda _: True,
                safer_feature_name=safe_feature_name,
            )
            .add_new_key("cancel_editing", lambda _: None, feature_name=feature_name),
            "select_an_option_to_continue",
            feature_name=feature_name,
        )

    @staticmethod
    def edit_rare_tickets(save_file: core.SaveFile):
        color.color_print_key("rare_ticket_warning")
        name = core.core_data.get_gatya_item_names(save_file).get_name(21)
        go_safe = BasicItems.should_go_safer_feature(
            "rare_tickets_l", "rare_ticket_trade_l"
        )
        if go_safe is None:
            return
        if go_safe:
            return edits.rare_ticket_trade.RareTicketTrade.rare_ticket_trade(save_file)

        original_amount = save_file.rare_tickets
        save_file.rare_tickets = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "rare_tickets"),
            save_file.rare_tickets,
            prompt.MaxValue.i32(core.core_data.max_value_manager.rare_tickets),
        )
        change = save_file.rare_tickets - original_amount
        core.BackupMetaData(save_file).add_managed_item(
            core.ManagedItem.from_change(change, core.ManagedItemType.RARE_TICKET)
        )

    @staticmethod
    def edit_platinum_tickets(save_file: core.SaveFile):
        color.color_print_key("platinum_ticket_warning")
        name = core.core_data.get_gatya_item_names(save_file).get_name(29)
        go_safer = BasicItems.should_go_safer_feature(
            "platinum_tickets_l", "platinum_shards_l"
        )
        if go_safer is None:
            return
        if go_safer:
            return edits.basic_items.BasicItems.edit_platinum_shards(save_file)

        original_amount = save_file.platinum_tickets
        save_file.platinum_tickets = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "platinum_tickets"),
            save_file.platinum_tickets,
            prompt.MaxValue.i32(core.core_data.max_value_manager.platinum_tickets),
        )
        change = save_file.platinum_tickets - original_amount
        core.BackupMetaData(save_file).add_managed_item(
            core.ManagedItem.from_change(change, core.ManagedItemType.PLATINUM_TICKET)
        )

    @staticmethod
    def edit_legend_tickets(save_file: core.SaveFile):
        should_exit = not prompt.confirm("legend_ticket_warning")
        if should_exit:
            return
        name = core.core_data.get_gatya_item_names(save_file).get_name(145)
        original_amount = save_file.legend_tickets
        save_file.legend_tickets = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "legend_tickets"),
            save_file.legend_tickets,
            prompt.MaxValue.i32(core.core_data.max_value_manager.legend_tickets),
        )
        change = save_file.legend_tickets - original_amount
        core.BackupMetaData(save_file).add_managed_item(
            core.ManagedItem.from_change(change, core.ManagedItemType.LEGEND_TICKET)
        )

    @staticmethod
    def edit_platinum_shards(save_file: core.SaveFile):
        name = core.core_data.get_gatya_item_names(save_file).get_name(157)
        platinum_ticket_amount = save_file.platinum_tickets
        max_value = (
            core.core_data.max_value_manager.platinum_tickets - platinum_ticket_amount
        ) * 10 + 9

        max_value = max(0, max_value)
        save_file.platinum_shards = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "platinum_shards"),
            save_file.platinum_shards,
            prompt.MaxValue.i32(max_value),
        )

    @staticmethod
    def edit_np(save_file: core.SaveFile):
        name = core.core_data.get_gatya_item_names(save_file).get_name(7)
        save_file.np = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "np"),
            save_file.np,
            prompt.MaxValue.i32(core.core_data.max_value_manager.np),
        )

    @staticmethod
    def edit_leadership(save_file: core.SaveFile):
        name = core.core_data.get_gatya_item_names(save_file).get_name(105)
        save_file.leadership = dialog_creator.edit_int_raw(
            BasicItems.get_name(name, "leadership"),
            save_file.leadership,
            prompt.MaxValue.i16(core.core_data.max_value_manager.leadership),
        )

    @staticmethod
    def edit_battle_items(save_file: core.SaveFile):
        edit_battle_items(save_file.battle_items, save_file)

    @staticmethod
    def edit_battle_items_endless(save_file: core.SaveFile):
        edit_endless_battle_items(save_file.battle_items, save_file)

    @staticmethod
    def edit_catamins(save_file: core.SaveFile):
        names_o = core.core_data.get_gatya_item_names(save_file)
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(6)
        if items is None:
            return
        names: list[str] = []
        for item in items:
            name = names_o.get_name(item.id)
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_catamin_name", id=item.id
                )
            names.append(name)
        values = dialog_creator.edit_ints_key(
            "catamins",
            names,
            save_file.catamins,
            prompt.MaxValue.i32(core.core_data.max_value_manager.catamins),
        )
        save_file.catamins = values

    @staticmethod
    def edit_catseyes(save_file: core.SaveFile):
        names_o = core.core_data.get_gatya_item_names(save_file)
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(5)
        if items is None:
            return
        names: list[str] = []
        for item in items:
            name = names_o.get_name(item.id)
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_catseye_name", id=item.id
                )
            names.append(name)

        values = dialog_creator.edit_ints_key(
            "catseyes",
            names,
            save_file.catseyes,
            prompt.MaxValue.i32(core.core_data.max_value_manager.catseyes),
        )
        save_file.catseyes = values

    @staticmethod
    def edit_treasure_chests(save_file: core.SaveFile):
        names_o = core.core_data.get_gatya_item_names(save_file)
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(
            GatyaItemCategory.TREASURE_CHESTS
        )
        if items is None:
            return
        names: list[str] = []
        for item in items[: len(save_file.treasure_chests)]:
            name = names_o.get_name(item.id)
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_treasure_chest_name", id=item.id
                )
            names.append(name)

        values = dialog_creator.edit_ints_key(
            "treasure_chests",
            names,
            save_file.treasure_chests,
            prompt.MaxValue.i32(core.core_data.max_value_manager.treasure_chests),
        )
        save_file.treasure_chests = values

    @staticmethod
    def edit_catfruit(save_file: core.SaveFile):
        names = core.Matatabi(save_file).get_names()
        if names is None:
            return
        new_names: list[str] = []
        for i, name in enumerate(names):
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_catfruit_name", id=i
                )
            new_names.append(name)
        names = new_names

        extra = len(save_file.catfruit) - len(names)
        if extra > 0:
            for i in range(extra):
                names.append(
                    core.core_data.local_manager.get_key(
                        "unknown_catfruit_name", id=i + len(names)
                    )
                )

        if save_file.game_version < 110400:
            max_value = core.core_data.max_value_manager.catfruit_old
            max = dialog_creator.CumulativeMax.new(prompt.MaxValue.i32(max_value))
        else:
            max_value = prompt.MaxValue.i32(
                core.core_data.max_value_manager.catfruit_new
            )
            max = max_value

        names = names[: len(save_file.catfruit)]

        values = dialog_creator.edit_ints_key(
            "catfruit", names, save_file.catfruit, max
        )
        save_file.catfruit = values

    @staticmethod
    def set_restart_pack(save_file: core.SaveFile):
        save_file.restart_pack = 1
        name = core.core_data.get_gatya_item_names(save_file).get_name(123)
        color.color_print_key("value_gave", name=name)

    @staticmethod
    def edit_inquiry_code(save_file: core.SaveFile):
        should_exit = not prompt.confirm("inquiry_code_warning")
        if should_exit:
            return
        item_name = save_file.get_localizable().get("autoSave_txt5")
        save_file.inquiry_code = dialog_creator.edit_str_raw(
            BasicItems.get_name(item_name, "inquiry_code"),
            save_file.inquiry_code,
        )

    @staticmethod
    def edit_password_refresh_token(save_file: core.SaveFile):
        should_exit = not prompt.confirm("password_refresh_token_warning")
        if should_exit:
            return
        save_file.password_refresh_token = dialog_creator.edit_str_key(
            "password_refresh_token",
            save_file.password_refresh_token,
        )

    @staticmethod
    def edit_scheme_items(save_file: core.SaveFile):
        edit_scheme_items(save_file.scheme_items, save_file)

    @staticmethod
    def edit_engineers(save_file: core.SaveFile):
        edits.ototo.edit_engineers(save_file.ototo, save_file)

    @staticmethod
    def edit_base_materials(save_file: core.SaveFile):
        edits.ototo.edit_base_materials(save_file.ototo.base_materials, save_file)

    @staticmethod
    def edit_rare_gatya_seed(save_file: core.SaveFile):
        edit_rare_seed(save_file.gatya)

    @staticmethod
    def edit_normal_gatya_seed(save_file: core.SaveFile):
        edit_normal_seed(save_file.gatya)

    @staticmethod
    def edit_event_gatya_seed(save_file: core.SaveFile):
        edit_event_seed(save_file.gatya)

    @staticmethod
    def edit_unlocked_slots(save_file: core.SaveFile):
        edit_lineup_slots(save_file.lineups)

    @staticmethod
    def edit_labyrinth_medals(save_file: core.SaveFile):
        names_o = core.core_data.get_gatya_item_names(save_file)
        items = core.core_data.get_gatya_item_buy(save_file).get_by_category(11)
        if items is None:
            return
        names: list[str] = []
        for item in items:
            name = names_o.get_name(item.id)
            if name is None:
                name = core.core_data.local_manager.get_key(
                    "unknown_labyrinth_medal_name", id=item.id
                )
            names.append(name)

        values = dialog_creator.edit_ints_key(
            "labyrinth_medals",
            names,
            save_file.labyrinth_medals,
            prompt.MaxValue.i32(core.core_data.max_value_manager.labyrinth_medals),
        )
        save_file.labyrinth_medals = values

    @staticmethod
    def edit_special_skills(save_file: core.SaveFile):
        edit_skills(save_file.special_skills, save_file)

    @staticmethod
    def unlock_equip_menu(save_file: core.SaveFile):
        save_file.unlock_equip_menu()
        color.color_print_key("equip_menu_unlocked")

    @staticmethod
    def allow_filibuster_stage_reclearing(save_file: core.SaveFile):
        save_file.filibuster_stage_enabled = True
        save_file.filibuster_stage_id = random.randint(0, 47)
        color.color_print_key("filibuster_stage_reclearing_allowed")


def edit_battle_items(items: core.BattleItems, save_file: core.SaveFile):
    group_name = save_file.get_localizable().get("shop_category1")
    if group_name is None:
        group_name = core.core_data.local_manager.get_key("battle_items")
    item_names = items.get_names(save_file)
    if item_names is None:
        return
    current_values = [item.amount for item in items.items]
    values = dialog_creator.edit_ints_raw(
        group_name,
        item_names,
        current_values,
        prompt.MaxValue.i32(core.core_data.max_value_manager.battle_items),
    )
    for i, value in enumerate(values):
        items.items[i].amount = value


def edit_endless_battle_items(items: core.BattleItems, save_file: core.SaveFile):
    item_names = items.get_names(save_file)
    if item_names is None:
        return

    current_values = [
        item.endless_item.get_endless_duration_formatted() for item in items.items
    ]

    options = prompt.choose_many(
        [
            core.localize("endless_item_item", item=item, int=val, escape=False)
            for item, val in zip(item_names, current_values, strict=False)
        ],
        "select_option",
    )

    if options is None:
        return

    individual = prompt.choose(
        prompt.keys(["individual", "all_at_once"]), "edit_endless_q"
    )
    if individual is None:
        return

    all_at_once = individual == 1

    infinity_str = core.localize("infinity")

    if all_at_once:
        val = prompt.text("enter_duration_minutes")
        if val is None:
            return

        if val.lower() == infinity_str.lower():
            val = inf
        else:
            try:
                val = float(val)
            except ValueError:
                return

        for item in items.items:
            item.endless_item.set_duration_mins(val, 0)
    else:
        for opt in options:
            val = prompt.text("enter_duration_minutes_item", item=item_names[opt])
            if val is None:
                return

            if val.lower() == infinity_str.lower():
                val = inf
            else:
                try:
                    val = float(val)
                except ValueError:
                    color.color_print_key("invalid_minute_count")
                    continue

            items.items[opt].endless_item.set_duration_mins(val, 0)

    color.color_print_key("endless_items_success")


def edit_lineup_slots(lineups: core.LineUps):
    lineups.unlocked_slots = dialog_creator.edit_int_key(
        "unlocked_slots",
        lineups.unlocked_slots,
        prompt.MaxValue.i8(lineups.slot_names_length),
    )


def edit_rare_seed(gatya: core.Gatya):
    gatya.rare_seed = dialog_creator.edit_int_key(
        "rare_gatya_seed", gatya.rare_seed, prompt.MaxValue.u32().hide_max()
    )


def edit_normal_seed(gatya: core.Gatya):
    gatya.normal_seed = dialog_creator.edit_int_key(
        "normal_gatya_seed",
        gatya.normal_seed,
        prompt.MaxValue.u32().hide_max(),
    )


def edit_event_seed(gatya: core.Gatya):
    gatya.event_seed = dialog_creator.edit_int_key(
        "event_gatya_seed",
        gatya.event_seed,
        prompt.MaxValue.u32().hide_max(),
    )


def edit_scheme_items(scheme: core.SchemeItems, save_file: core.SaveFile):
    item_names = core.core_data.get_gatya_item_names(save_file)
    localizable = save_file.get_localizable()
    scheme_data = core.core_data.get_game_data_getter(save_file).download(
        "DataLocal", "schemeItemData.tsv"
    )
    if scheme_data is None:
        return
    csv = core.CSV(scheme_data, "\t")
    scheme_items: dict[int, core.game.catbase.scheme_items.SchemeDataItem] = {}
    for line in csv.lines[1:]:
        scheme_items[line[0].to_int()] = core.game.catbase.scheme_items.SchemeDataItem(
            line[0].to_int(),
            line[1].to_int(),
            line[2].to_int(),
            line[3].to_int(),
            line[4].to_int(),
            line[5].to_int(),
            line[6].to_int(),
            line[7].to_int(),
            line[8].to_int(),
            line[9].to_int(),
            line[10].to_int(),
        )

    options: list[str] = []
    for item in scheme_items.values():
        scheme_name = item.get_name(localizable)
        if scheme_name is None:
            return
        string = "\n\t"
        if item.is_cat():
            cat_names = core.Cat.get_names(item.item_id, save_file)
            if cat_names:
                cat_name = cat_names[0]
                string += scheme_name.replace("%@", cat_name)
        else:
            item_name = item_names.get_name(item.item_id)
            if item_name:
                string += scheme_name
                first_index = string.find("%@")
                second_index = string.find("%@", first_index + 1)
                string = (
                    string[:first_index]
                    + str(item.number)
                    + " "
                    + item_name
                    + string[second_index + 2 :]
                )
        string = string.replace("<br>", "\n\t")
        options.append(string)

    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key(
            "gain_scheme_items",
            lambda _: add_scheme_items(scheme, options, scheme_items),
        )
        .add_new_key(
            "remove_scheme_items",
            lambda _: remove_scheme_items(scheme, options, scheme_items),
        ),
        "gain_remove_scheme_items",
    )


def add_scheme_items(
    scheme: core.SchemeItems,
    options: list[str],
    scheme_items: dict[int, core.game.catbase.scheme_items.SchemeDataItem],
):
    scheme_ids = prompt.choose_many(
        options,
        dialog="scheme_items_select_gain",
    )
    if scheme_ids is None:
        return
    for option_id in scheme_ids:
        scheme_id = list(scheme_items.keys())[option_id]
        if scheme_id not in scheme.to_obtain:
            scheme.to_obtain.append(scheme_id)
        if scheme_id in scheme.received:
            scheme.received.remove(scheme_id)

    color.color_print_key("scheme_items_edit_success")


def remove_scheme_items(
    scheme: core.SchemeItems,
    options: list[str],
    scheme_items: dict[int, core.game.catbase.scheme_items.SchemeDataItem],
):
    scheme_ids = prompt.choose_many(
        options,
        dialog="scheme_items_select_remove",
    )
    if scheme_ids is None:
        return
    for option_id in scheme_ids:
        scheme_id = list(scheme_items.keys())[option_id]
        if scheme_id in scheme.to_obtain:
            scheme.to_obtain.remove(scheme_id)
        if scheme_id in scheme.received:
            scheme.received.remove(scheme_id)

    color.color_print_key("scheme_items_edit_success")


def edit_skills_individually(
    special_skills: core.SpecialSkills,
    ids: list[int],
    names: list[str],
    save_file: core.SaveFile,
):
    skills = special_skills.get_valid_skills()
    ability_data = core.core_data.get_ability_data(save_file)
    if ability_data.ability_data is None:
        return
    for id in ids:
        color.color_print_key(
            "selected_skill_upgrades",
            name=names[id],
            base_level=skills[id].upgrade.base + 1,
            plus_level=skills[id].upgrade.plus,
        )
        ability = ability_data.get_ability_data_item(id)
        if ability is None:
            continue
        upgrade, should_exit = edits.cat_editor.get_user_upgrade(
            ability.max_base_level - 1, ability.max_plus_level
        )
        if should_exit:
            return
        if upgrade is not None:
            special_skills.set_upgrade(id, upgrade)
            color.color_print_key(
                "selected_skill_upgraded",
                name=names[id],
                base_level=skills[id].upgrade.base + 1,
                plus_level=skills[id].upgrade.plus,
            )


def edit_skills_at_once(
    special_skills: core.SpecialSkills,
    ids: list[int],
    save_file: core.SaveFile,
    names: list[str],
):
    skills = special_skills.get_valid_skills()
    ability_data = core.core_data.get_ability_data(save_file)
    if ability_data.ability_data is None:
        return
    max_base_level = max(
        [ability.max_base_level for ability in ability_data.ability_data]
    )
    max_plus_level = max(
        [ability.max_plus_level for ability in ability_data.ability_data]
    )
    upgrade, should_exit = edits.cat_editor.get_user_upgrade(
        max_base_level - 1, max_plus_level
    )
    if should_exit or upgrade is None:
        return
    disable_maxes = core.core_data.config.get_bool(core.ConfigKey.DISABLE_MAXES)
    for id in ids:
        max_base_level = ability_data.ability_data[id].max_base_level - 1
        max_plus_level = ability_data.ability_data[id].max_plus_level
        if disable_maxes:
            max_base_level = None
            max_plus_level = None

        special_skills.set_upgrade(
            id,
            upgrade.copy(),
            max_base=max_base_level,
            max_plus=max_plus_level,
        )

        color.color_print_key(
            "selected_skill_upgraded",
            name=names[id],
            base_level=skills[id].upgrade.base + 1,
            plus_level=skills[id].upgrade.plus,
        )


def edit_skills(special_skills: core.SpecialSkills, save_file: core.SaveFile):
    names_o = core.core_data.get_gatya_item_names(save_file)
    items = core.core_data.get_gatya_item_buy(save_file).get_by_category(2)
    if items is None:
        return
    names: list[str] = []
    for item in items:
        name = names_o.get_name(item.id)
        if name is None:
            return
        names.append(name)
    ids = prompt.choose_many(names, "special_skills_dialog")
    if not ids:
        return
    if len(ids) == 1:
        edit_skills_individually(special_skills, ids, names, save_file)
    else:
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "upgrade_individual_skill",
                lambda _: edit_skills_individually(
                    special_skills, ids, names, save_file
                ),
            )
            .add_new_key(
                "upgrade_all_skills",
                lambda _: edit_skills_at_once(special_skills, ids, save_file, names),
            ),
            "upgrade_skills_select_mod",
        )

    edits.cat_editor.CatEditor.set_rank_up_sale(save_file)

    color.color_print_key("skills_edited")
