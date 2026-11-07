from bcsfe import core
from bcsfe.cli import color, prompt


def reset_gambling_events(save_file: core.SaveFile):
    save_file.wildcat_slots.reset()
    color.color_print_key("reset_wildcat_slots")
    save_file.cat_scratcher.reset()
    color.color_print_key("reset_cat_scratcher")


def edit_medals(save_file: core.SaveFile):
    medals = save_file.medals
    medal_names = core.core_data.get_medal_names(save_file)
    if medal_names.medal_names is None:
        return
    options = ["add_medals", "remove_medals"]
    choice = prompt.choose(prompt.keys(options), dialog="medal_add_remove_dialog")
    if choice is None:
        return
    add_medals = choice == 0

    medals_to_choose_from: list[tuple[int, str]] = []
    for i, medal in enumerate(medal_names.medal_names):
        if len(medal) == 0:
            continue
        if medals.has_medal(i) == add_medals:
            continue
        key = "medal_string"
        string = core.core_data.local_manager.get_key(
            key, medal_name=medal[0], medal_req=medal[1]
        )
        medals_to_choose_from.append((i, string))
    if len(medals_to_choose_from) == 0:
        return
    options = [medal[1] for medal in medals_to_choose_from]
    choices = prompt.choose_many(options, dialog="select_medals")
    if choices is None:
        return
    for choice in choices:
        medal_id = medals_to_choose_from[choice][0]
        if add_medals:
            medals.add_medal(medal_id)
        else:
            medals.remove_medal(medal_id)

    if add_medals:
        color.color_print_key("medals_added")
    else:
        color.color_print_key("medals_removed")


def edit_missions(save_file: core.SaveFile):
    missions = save_file.missions

    names = core.core_data.get_mission_names(save_file)
    conditions = core.core_data.get_mission_conditions(save_file)
    if names.names is None or conditions.conditions is None:
        return
    options: list[str] = []
    mssion_ids: list[int] = []
    for mission_id, name in names.names.items():
        if mission_id in missions.clear_states:
            name = name.split("<br>")[0]
            condition = conditions.conditions.get(mission_id)
            if not condition:
                continue
            name = name.replace("%d", str(condition.progress_count))
            if "%@" in name and len(condition.conditions_value) > 2:
                name = name.replace("%@", str(condition.conditions_value[2]))
            options.append(name)
            mssion_ids.append(mission_id)

    re_claim = prompt.choose(
        prompt.keys(["complete_reward", "complete_claim", "uncomplete"]),
        dialog="select_mission_claim",
    )
    if re_claim is None:
        return

    choices = prompt.choose_many(options, dialog="select_missions")
    if choices is None:
        return
    for choice in choices:
        mission_id = mssion_ids[choice]
        if re_claim == 0:
            missions.clear_states[mission_id] = 2
            condition = conditions.get_condition(mission_id)
            if condition is not None:
                missions.requirements[mission_id] = condition.progress_count
        elif re_claim == 1:
            missions.clear_states[mission_id] = 4
            condition = conditions.get_condition(mission_id)
            if condition is not None:
                missions.requirements[mission_id] = condition.progress_count
        elif re_claim == 2:
            missions.clear_states[mission_id] = 0
            if mission_id in missions.requirements:
                missions.requirements[mission_id] = 0

    color.color_print_key("missions_edited")


def edit_gold_pass(save_file: core.SaveFile):
    club = save_file.officer_pass.gold_pass

    officer_id = color.color_input_key("gold_pass_dialog").strip()
    if not officer_id:
        officer_id = core.NyankoClub.get_random_officer_id()

    if officer_id == "-1":
        officer_id = -1
    else:
        try:
            officer_id = int(officer_id)
        except ValueError:
            officer_id = core.NyankoClub.get_random_officer_id()
        officer_id = prompt.MaxValue.i32().clamp(officer_id)

    if officer_id == -1:
        club.remove_gold_pass(save_file)
        color.color_print_key("gold_pass_remove_success")
    else:
        club.get_gold_pass(officer_id, 30, save_file)
        color.color_print_key("gold_pass_get_success", id=officer_id)


def fix_officer_pass_crash(save_file: core.SaveFile):
    officer_pass = save_file.officer_pass
    officer_pass.reset(save_file)

    color.color_print_key("officer_pass_fixed")


def edit_playtime(save_file: core.SaveFile):
    play_time = core.PlayTime(save_file.officer_pass.play_time)
    color.color_print_key(
        "playtime_current",
        hours=play_time.hours,
        minutes=play_time.just_minutes,
        seconds=play_time.just_seconds,
        frames=play_time.frames,
    )
    hours = prompt.number("playtime_hours_prompt", max=prompt.MaxValue.i32().hide_max())
    if hours is None:
        return
    minutes = prompt.number(
        "playtime_minutes_prompt", max=prompt.MaxValue.i32().hide_max()
    )
    if minutes is None:
        return
    seconds = prompt.number(
        "playtime_seconds_prompt", max=prompt.MaxValue.i32().hide_max()
    )
    if seconds is None:
        return

    play_time = core.PlayTime.from_hours_mins_secs(hours, minutes, seconds)
    save_file.officer_pass.play_time = play_time.frames
    color.color_print_key(
        "playtime_edited",
        hours=play_time.hours,
        minutes=play_time.just_minutes,
        seconds=play_time.just_seconds,
        frames=play_time.frames,
    )


def edit_rank_rewards(rewards: core.UserRankRewards, save_file: core.SaveFile):
    claim_choice = prompt.choose(
        prompt.keys(["claim", "unclaim", "fix_claimed"]),
        dialog="claim_or_unclaim_ur",
    )

    if claim_choice is None:
        return

    rank_gifts = core.core_data.get_rank_gifts(save_file)
    if rank_gifts.rank_gift is None:
        return

    user_rank = save_file.calculate_user_rank()

    if claim_choice == 2:
        for rank_gift in rank_gifts.rank_gift:
            reward = rewards.rewards[rank_gift.index]
            if rank_gift.threshold > user_rank:
                reward.claimed = False

        color.color_print_key("ur_fix_claimed_success")
        return

    selected_rank_gifts: list[core.game.catbase.user_rank_rewards.RankGift] = (
        rank_gifts.rank_gift.copy()
    )
    descriptions = core.core_data.get_rank_gift_descriptions(save_file)

    selected_rank_gifts.sort(key=lambda rank_gift: rank_gift.threshold)

    new_selected_rank_gifts: list[core.game.catbase.user_rank_rewards.RankGift] = []

    for rank_gift in selected_rank_gifts:
        reward = rewards.rewards[rank_gift.index]
        if reward.claimed and claim_choice == 0:
            continue
        if not reward.claimed and claim_choice == 1:
            continue
        if rank_gift.threshold > user_rank:
            continue
        new_selected_rank_gifts.append(rank_gift)

    selected_rank_gifts = new_selected_rank_gifts

    selected_descriptions: list[str] = []
    for rank_gift in selected_rank_gifts:
        name = rank_gift.get_name(descriptions)
        if name is None:
            return
        description = name.replace("<br>", " ")
        # remove span tags
        start = description.find("<")
        while start != -1:
            end = description.find(">")
            description = description[:start] + description[end + 1 :]
            start = description.find("<")

        selected_descriptions.append(
            core.core_data.local_manager.get_key(
                "ur_string",
                description=description,
                rank=rank_gift.threshold,
            )
        )

    ids = prompt.choose_many(selected_descriptions, dialog="select_ur")
    if ids is None:
        return
    for id in ids:
        index = selected_rank_gifts[id].index
        rewards.set_claimed(index, claim_choice == 0)

    if claim_choice == 0:
        color.color_print_key("ur_claimed_success")
    else:
        color.color_print_key("ur_unclaimed_success")


def edit_user_rank_rewards(save_file: core.SaveFile):
    user_rank_rewards = save_file.user_rank_rewards
    edit_rank_rewards(user_rank_rewards, save_file)
