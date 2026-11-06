from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt

type ChaptersType = (
    core.EventChapters
    | core.GauntletChapters
    | core.LegendQuestChapters
    | core.ZeroLegendsChapters
    | core.Chapters
)


def get_total_maps(chapters: ChaptersType) -> int:
    if isinstance(chapters, core.EventChapters):
        return chapters.get_lengths()[1]
    return len(chapters.chapters)


def unclear_stage(
    chapters: ChaptersType,
    map: int,
    star: int,
    stage: int,
    type: int | None = None,
) -> bool:
    if isinstance(chapters, core.EventChapters):
        if type is None:
            raise ValueError("Type must be specified for EventChapters!")
        return chapters.unclear_stage(type, map, star, stage)
    else:
        return chapters.unclear_stage(map, star, stage)


def clear_stage(
    chapters: ChaptersType,
    map: int,
    star: int,
    stage: int,
    clear_amount: int = 1,
    overwrite_clear_progress: bool = False,
    type: int | None = None,
    ensure_cleared_only: bool = False,
) -> bool:
    if isinstance(chapters, core.EventChapters):
        if type is None:
            raise ValueError("Type must be specified for EventChapters!")

        return chapters.clear_stage(
            type, map, star, stage, clear_amount, overwrite_clear_progress
        )
    else:
        return chapters.clear_stage(
            map,
            star,
            stage,
            clear_amount,
            overwrite_clear_progress,
            ensure_cleared_only=ensure_cleared_only,
        )


def unclear_rest(
    chapters: ChaptersType,
    stages: list[int],
    stars: int,
    id: int,
    type: int | None = None,
):
    if isinstance(chapters, core.EventChapters):
        if type is None:
            raise ValueError("Type must be specified for EventChapters!")
        chapters.unclear_rest(stages, stars, id, type)
    else:
        chapters.unclear_rest(stages, stars, id)


def get_total_stars(
    map_option: core.MapOption,
    base_index: int,
    chapters: ChaptersType,
    id: int,
    type: int | None = None,
) -> int:

    max_stars = get_max_stars(chapters, id, type)

    map_option_stars = map_option.get_map(base_index + id)
    if map_option_stars is not None:
        return min(max_stars, map_option_stars.crown_count)
    return max_stars


def get_max_max_stars(
    map_option: core.MapOption,
    base_index: int,
    ids: list[int],
    chapters: ChaptersType,
    type: int | None = None,
) -> int:
    m = 0
    for id in ids:
        val = get_total_stars(map_option, base_index, chapters, id, type)
        if val > m:
            m = val

    return m


def get_max_stars(
    chapters: ChaptersType,
    id: int,
    type: int | None = None,
) -> int:

    if isinstance(chapters, core.EventChapters):
        if type is None:
            raise ValueError("Type must be specified for EventChapters!")
        max_stars = chapters.get_total_stars(type, id)
    else:
        max_stars = chapters.get_total_stars(id)

    return max_stars


def get_total_stages(
    chapters: ChaptersType, id: int, star: int, type: int | None = None
):
    if isinstance(chapters, core.EventChapters):
        if type is None:
            raise ValueError("Type must be specified for EventChapters!")
        total_stars = chapters.get_total_stages(type, id, star)
    else:
        total_stars = chapters.get_total_stages(id, star)

    return total_stars


def select_maps(
    save_file: core.SaveFile,
    chapters: ChaptersType,
    letter_code: str,
    base_index: int,
    no_r_prefix: bool = False,
) -> list[int] | None:
    map_names = core.MapNames(
        save_file, letter_code, no_r_prefix=no_r_prefix, base_index=base_index
    )
    names: dict[int, str | None] = {}
    for id, name in map_names.map_names.items():
        if id >= get_total_maps(chapters):
            continue
        names[id] = name

    return select_map_names(names)


def select_maps_stars(
    save_file: core.SaveFile,
    map_option: core.MapOption,
    chapters: ChaptersType,
    letter_code: str,
    base_index: int,
    type: int | None = None,
    no_r_prefix: bool = False,
) -> list[tuple[int, int]] | None:
    map_names = core.MapNames(
        save_file, letter_code, no_r_prefix=no_r_prefix, base_index=base_index
    )
    names: dict[int, str | None] = {}
    for id, name in map_names.map_names.items():
        if id >= get_total_maps(chapters):
            continue

        for star in range(get_total_stars(map_option, base_index, chapters, id, type)):
            names[id * 10 + star] = core.localize(
                "map_name_star", name=name, star=star + 1
            )

    ids = select_map_names(names)
    if ids is None:
        return None

    new_ids: list[tuple[int, int]] = []

    for id in ids:
        map_id = id // 10
        star_index = id % 10

        new_ids.append((map_id, star_index))

    return new_ids


def clear_whole_chapter(
    chapters: ChaptersType, local_map_id: int, star: int, type: int | None
):
    clear_count = ask_clear_amount()
    if clear_count is None:
        return None

    for stage in range(get_total_stages(chapters, local_map_id, star, type)):
        clear_stage(chapters, local_map_id, star, stage, clear_count, type=type)


def edit_stage_individual(
    chapters: ChaptersType,
    local_map_id: int,
    star: int,
    type: int | None,
    stage_ids: list[int],
    stage_names: list[str],
):
    for stage in stage_ids:
        print()
        if stage < len(stage_names):
            stage_name = stage_names[stage]
        else:
            stage_name = None
        print_current_stage(stage_name, stage)
        clear_count = ask_clear_amount()
        if clear_count is None:
            return None
        clear_stage(chapters, local_map_id, star, stage, clear_count, type=type)


def edit_stage_many(
    chapters: ChaptersType,
    local_map_id: int,
    star: int,
    type: int | None,
    stage_ids: list[int],
):
    clear_count = ask_clear_amount()
    if clear_count is None:
        return None
    for stage in stage_ids:
        clear_stage(chapters, local_map_id, star, stage, clear_count, type=type)


def edit_specific_stages(
    chapters: ChaptersType,
    map_names: core.MapNames,
    local_map_id: int,
    star: int,
    type: int | None,
):
    stage_ids = ask_stages(map_names, local_map_id)

    if stage_ids is None:
        return None

    stage_names = core.EventChapters.get_stage_names(map_names, local_map_id)
    if stage_names is None:
        stage_names = []

    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key(
            "each_stage_individually",
            lambda _: edit_stage_individual(
                chapters, local_map_id, star, type, stage_ids, stage_names
            ),
        )
        .add_new_key(
            "stage_all_at_once",
            lambda _: edit_stage_many(chapters, local_map_id, star, type, stage_ids),
        ),
        "set_clear_count_stage_q",
    )


def edit_chapters2_clear_count(
    save_file: core.SaveFile,
    chapters: ChaptersType,
    letter_code: str,
    base_index: int,
    type: int | None = None,
    no_r_prefix: bool = False,
) -> None:

    map_names = core.MapNames(
        save_file, letter_code, no_r_prefix=no_r_prefix, base_index=base_index
    )

    map_option = core.MapOption.from_save(save_file)
    if map_option is None:
        return None

    map_choices = select_maps_stars(
        save_file, map_option, chapters, letter_code, base_index, type, no_r_prefix
    )
    if map_choices is None:
        return None

    clear_all = is_edit_all(len(map_choices))
    if clear_all is None:
        return None

    if clear_all == 0:
        clear_count = ask_clear_amount()
        if clear_count is None:
            return None

        for local_map_id, star in map_choices:
            total_stages = get_total_stages(chapters, local_map_id, star, type)
            for stage in range(total_stages):
                clear_stage(chapters, local_map_id, star, stage, clear_count, type=type)
    else:
        for local_map_id, star in map_choices:
            print()
            print_current_chapter(
                core.localize(
                    "map_name_star",
                    star=star,
                    name=map_names.map_names.get(local_map_id),
                ),
                local_map_id,
            )
            dialog_creator.single_select_key(
                dialog_creator.Actions[None]
                .new()
                .add_new_key(
                    "edit_whole_chapter",
                    lambda _: clear_whole_chapter(chapters, local_map_id, star, type),
                )
                .add_new_key(
                    "edit_special_stages",
                    lambda _: edit_specific_stages(
                        chapters, map_names, local_map_id, star, type
                    ),
                ),
                "edit_chapter_q",
            )


def is_clear_all(map_choices_len: int) -> bool | None:
    if map_choices_len <= 1:
        return False

    return dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("clear_all", lambda _: True)
        .add_new_key("handle_individually", lambda _: False),
        "clear_chapters_q",
    )


def is_unclear_all(map_choices_len: int) -> bool | None:
    if map_choices_len <= 1:
        return False

    return dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("unclear_all", lambda _: True)
        .add_new_key("handle_individually", lambda _: False),
        "unclear_chapters_q",
    )


def is_edit_all(map_choices_len: int) -> bool | None:
    if map_choices_len <= 1:
        return False

    return dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("edit_map_all", lambda _: True)
        .add_new_key("handle_individually", lambda _: False),
        "edit_chapters_q_all",
    )


def clear_whole_chapter_unclear(
    map_option: core.MapOption,
    base_index: int,
    chapters: ChaptersType,
    local_map_id: int,
    type: int | None,
    allow_unclear: bool,
):
    max_stars = get_total_stars(map_option, base_index, chapters, local_map_id, type)
    if allow_unclear:
        stars = ask_stars_unclear(max_stars)
    else:
        stars = ask_stars(max_stars)
    if stars is None:
        return None

    unclear_rest(
        chapters,
        [0],
        max(stars - 1, 0),
        local_map_id,
        type,
    )

    for star in range(stars):
        total_stages = get_total_stages(chapters, local_map_id, star, type)
        for stage in range(total_stages):
            clear_stage(
                chapters,
                local_map_id,
                star,
                stage,
                type=type,
                ensure_cleared_only=True,
            )


def clear_specific_stage_unclear(
    local_map_id: int,
    map_names: core.MapNames,
    map_option: core.MapOption,
    base_index: int,
    chapters: ChaptersType,
    type: int | None,
    allow_unclear: bool,
):
    stage_names = map_names.stage_names.get(local_map_id)
    stage_names = [
        stage_name
        for stage_name in stage_names or []
        if stage_name and stage_name != "＠"
    ]
    stage_id = ask_stages_stage_names_one(stage_names)
    if stage_id is None:
        return None

    max_stars = get_total_stars(map_option, base_index, chapters, local_map_id, type)

    if allow_unclear:
        stars = ask_stars_unclear(max_stars)
    else:
        stars = ask_stars(max_stars)
    if stars is None:
        return None

    unclear_rest(chapters, list(range(stage_id)), max(stars - 1, 0), local_map_id, type)

    for star in range(stars - 1):
        total_stages = get_total_stages(chapters, local_map_id, star, type)
        for stage in range(total_stages):
            clear_stage(
                chapters,
                local_map_id,
                star,
                stage,
                type=type,
                ensure_cleared_only=True,
            )

    for stage in range(stage_id + 1):
        clear_stage(
            chapters,
            local_map_id,
            stars - 1,
            stage,
            type=type,
            ensure_cleared_only=True,
        )


def edit_chapters2_progress(
    save_file: core.SaveFile,
    chapters: ChaptersType,
    letter_code: str,
    base_index: int,
    type: int | None = None,
    no_r_prefix: bool = False,
    allow_unclear: bool = False,
) -> None:
    map_names = core.MapNames(
        save_file, letter_code, no_r_prefix=no_r_prefix, base_index=base_index
    )

    map_choices = select_maps(save_file, chapters, letter_code, base_index, no_r_prefix)
    if map_choices is None:
        return None

    clear_all = is_clear_all(len(map_choices))
    if clear_all is None:
        return None

    map_option = core.MapOption.from_save(save_file)
    if map_option is None:
        return None

    if clear_all:
        max_stars = get_max_max_stars(
            map_option, base_index, map_choices, chapters, type
        )
        if allow_unclear:
            stars = ask_stars_unclear(max_stars, "max_stars")
        else:
            stars = ask_stars(max_stars, "max_stars")
        if stars is None:
            return None
        for local_map_id in map_choices:
            unclear_rest(
                chapters,
                [0],
                max(0, stars - 1),
                local_map_id,
                type,
            )
            for star in range(stars):
                total_stages = get_total_stages(chapters, local_map_id, star, type)
                for stage in range(total_stages):
                    clear_stage(
                        chapters,
                        local_map_id,
                        star,
                        stage,
                        type=type,
                        ensure_cleared_only=True,
                    )

        return None

    for local_map_id in map_choices:
        name = map_names.map_names.get(local_map_id)
        print_current_chapter(name, local_map_id)
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "clear_whole_chapter",
                lambda _: clear_whole_chapter_unclear(
                    map_option, base_index, chapters, local_map_id, type, allow_unclear
                ),
            )
            .add_new_key(
                "clear_to_specific_stage",
                lambda _: clear_specific_stage_unclear(
                    local_map_id,
                    map_names,
                    map_option,
                    base_index,
                    chapters,
                    type,
                    allow_unclear,
                ),
            ),
            "clear_whole_q",
        )


def edit_chapters(
    save_file: core.SaveFile,
    chapters: ChaptersType,
    letter_code: str,
    base_index: int,
    type: int | None = None,
    no_r_prefix: bool = False,
) -> dict[int, bool] | None:
    while True:
        # The actions only say which edit was picked; running the edit inside
        # them as well would run it twice (and made "finish" start an edit).
        choice = dialog_creator.single_select_key(
            dialog_creator.Actions[str]
            .new()
            .add_new_key("edit_progress_clear", lambda _: "clear")
            .add_new_key("edit_progress_unclear", lambda _: "unclear")
            .add_new_key("edit_clear_counts", lambda _: "counts")
            .add_new_key("finish", lambda _: "finish"),
            "edit_chapters_q",
        )
        if choice is None or choice == "finish":
            break

        if choice == "counts":
            edit_chapters2_clear_count(
                save_file, chapters, letter_code, base_index, type, no_r_prefix
            )
        else:
            edit_chapters2_progress(
                save_file,
                chapters,
                letter_code,
                base_index,
                type,
                no_r_prefix,
                allow_unclear=choice == "unclear",
            )
        color.color_print_key("map_chapters_edited")

    return None


def ask_stars(
    max_stars: int, dialog: str = "custom_star_count_per_chapter"
) -> int | None:
    if max_stars <= 1:
        return max_stars
    stars = prompt.number(dialog, min=1, max=prompt.MaxValue.always_cap(max_stars))
    if stars is None:
        return None
    return stars


def ask_stars_unclear(
    max_stars: int, dialog: str = "custom_star_count_per_chapter"
) -> int | None:
    stars = prompt.number(dialog, min=0, max=prompt.MaxValue.always_cap(max_stars))
    if stars is None:
        return None
    return stars


def ask_stages(map_names: core.MapNames, chapter_id: int) -> list[int] | None:
    stage_names = core.EventChapters.get_stage_names(map_names, chapter_id)
    if stage_names is None:
        return None

    color.color_print_key("select_stage")
    prompt.show_options(stage_names)

    choices = prompt.numbers("stages_select", min=1, max=len(stage_names))
    if choices is None:
        return None
    return [c - 1 for c in choices]


def ask_stages_stage_names(stage_names: list[str]) -> list[int] | None:
    val = ask_stages_stage_names_one(stage_names)
    if val is None:
        return None
    return list(range(val + 1))


def ask_stages_stage_names_one(stage_names: list[str]) -> int | None:
    new_stage_names: list[str] = []
    for stage in stage_names:
        if stage == "＠":
            continue
        new_stage_names.append(stage)
    stage_names = new_stage_names
    choice = prompt.choose(
        stage_names,
        dialog="select_stage_progress",
    )
    if choice is None:
        return None
    return choice


def ask_clear_amount() -> int | None:
    val = prompt.number(
        "clear_amount_enter",
        max=prompt.MaxValue.i16(core.core_data.max_value_manager.stage_clear_count),
    )

    return val


def edit_sol_chapters(save_file: core.SaveFile):
    edit_event_type_chapters(save_file, 0, "N", 0)


def edit_event_chapters(save_file: core.SaveFile):
    edit_event_type_chapters(save_file, 1, "S", 1000)


def edit_collab_chapters(save_file: core.SaveFile):
    edit_event_type_chapters(save_file, 2, "C", 2000)


def select_map_names(names_dict: dict[int, str | None]) -> list[int] | None:
    map_ids: list[int] = []
    names_list: list[str] = []
    names_dict = dict(sorted(names_dict.items()))
    ids = list(names_dict.keys())
    for id, map_name in names_dict.items():
        if map_name is None:
            map_name = core.core_data.local_manager.get_key("unknown_map_name", id=id)
        else:
            map_name = core.core_data.local_manager.get_key(
                "map_name", name=map_name, id=id, escape=False
            )
        names_list.append(map_name)

    while True:
        color.color_print_key("select_map")
        prompt.show_options(names_list)
        if names_list:
            example_name = names_list[0]
        else:
            example_name = ""
        usr_input = (
            color.color_input_key(
                "select_map_dialog", example=example_name, escape=False
            )
            .lower()
            .strip()
        )
        if usr_input == core.localize("quit_key"):
            return None
        if usr_input.lower() == core.localize("all").lower():
            usr_ids = list(range(1, len(names_list) + 1))
        elif usr_input.strip(" -0123456789"):
            usr_ids = None  # a name to search for
        else:
            usr_ids = prompt.parse_numbers(usr_input, min=1, max=len(names_list))
        if not usr_ids:
            found_names: list[tuple[int, str]] = []
            for i, name in enumerate(names_list):
                if usr_input.replace(" ", "_") in name.lower().strip().replace(
                    " ", "_"
                ):
                    true_id = ids[i]
                    found_names.append((true_id, name))

            if len(found_names) == 0:
                color.color_print_key("no_map_found", name=usr_input)
            elif len(found_names) == 1:
                id = found_names[0][0]
                true_id = ids[id]
                if true_id not in map_ids:
                    map_ids.append(true_id)
            else:
                selected_ids = prompt.choose_many(
                    [name for _, name in found_names],
                    dialog="select_map_from_names",
                )
                if selected_ids is None:
                    continue
                for i in selected_ids:
                    id = found_names[i][0]
                    true_id = ids[id]
                    if true_id not in map_ids:
                        map_ids.append(true_id)
        else:
            for id in usr_ids:
                id -= 1
                true_id = ids[id]
                if true_id not in map_ids:
                    map_ids.append(true_id)

        color.color_print_key("current_maps", maps=map_ids)

        for id in map_ids:
            name = names_dict[id]
            print_current_chapter(name, id)

        option = prompt.choose(
            prompt.keys(["keep_selecting", "remove_selection", "finish_selection"]),
            dialog="map_selection_q",
        )
        if option is None:
            return None
        if option == 0:
            continue
        if option == 1:
            map_ids.clear()
        else:
            break
    return map_ids


def print_current_chapter(name: str | None, id: int):
    if name is None:
        name = core.core_data.local_manager.get_key("unknown_map_name", id=id)
    color.color_print_key("current_sol_chapter", escape=False, name=name, id=id)


def print_current_stage(name: str | None, index: int):
    if name is None:
        name = core.core_data.local_manager.get_key("unknown_stage_name", index=index)
    color.color_print_key("current_stage_map", name=name, index=index)


def edit_event_type_chapters(
    save_file: core.SaveFile, type: int, letter_code: str, base_index: int
):
    edit_chapters(
        save_file,
        save_file.event_stages,
        letter_code,
        type=type,
        base_index=base_index,
    )
