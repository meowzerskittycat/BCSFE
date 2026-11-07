import time

from bcsfe import core
from bcsfe.cli import color, dialog_creator, edits, prompt


def edit_aku_chapters(save_file: core.SaveFile):
    aku = save_file.aku
    chapter = aku.chapters[0].chapters[0]

    clear_progress = edits.story.get_selected_chapter_progress(
        max_stages=len(chapter.stages)
    )
    if clear_progress is None:
        return

    if clear_progress > 1:
        individual_clear_count = edits.story.ask_if_individual_clear_counts()
        if individual_clear_count is None:
            return
    else:
        individual_clear_count = True

    if individual_clear_count:
        stage_names = core.StageNames(save_file, "DM", 49).stage_names
        if stage_names is None:
            return
        for i, stage in enumerate(chapter.stages[:clear_progress]):
            stage_name = stage_names[i]
            color.color_print_key("aku_current_stage", name=stage_name, id=i)
            clear_count = edits.story.ask_clear_count()
            if clear_count is None:
                return
            stage.clear_stage(clear_count)
    else:
        clear_count = edits.story.ask_clear_count()
        if clear_count is None:
            return
        for stage in chapter.stages[:clear_progress]:
            stage.clear_stage(clear_count)

    for i in range(clear_progress, len(chapter.stages)):
        chapter.stages[i].clear_stage(0)

    color.color_print_key("aku_clear_success")


def add_enigma_stages(enigma: core.Enigma, save_file: core.SaveFile):
    names = core.MapNames(save_file, "H", base_index=25000).map_names
    names_list: list[str] = []
    keys = list(names.keys())
    keys.sort()
    for id in keys:
        name = names[id]
        if name is None:
            name = core.core_data.local_manager.get_key("unknown_enigma_name", id=id)
        names_list.append(name)

    base_level = 25000

    color.color_print_key("current_enigma_stages")
    for stage in enigma.stages:
        name = names[stage.stage_id - base_level]
        if name is None:
            name = core.core_data.local_manager.get_key(
                "unknown_enigma_name", id=stage.stage_id
            )
        color.color_print_key("enigma_stage", name=name, id=stage.stage_id - base_level)

    if enigma.stages:
        wipe = prompt.confirm("wipe_enigma")
        if wipe is None:
            return
        if wipe:
            for stage in enigma.stages:
                id = stage.stage_id
                save_file.event_stages.chapter_completion_count[id] = 0
            enigma.stages = []

    ids = prompt.choose_many(
        names_list,
        "enigma_select",
    )
    if ids is None:
        return

    for enigma_id in ids:
        abs_id = enigma_id + base_level
        save_file.event_stages.chapter_completion_count[abs_id] = 0
        # TODO: level? they can go much higher than 3... not sure it really matters though
        stage = core.game.map.enigma.Stage(3, abs_id, 2, int(time.time()))
        enigma.stages.append(stage)

    color.color_print_key("enigma_success")


def edit_enigma(save_file: core.SaveFile):
    add_enigma_stages(save_file.enigma, save_file)


def edit_gauntlets(save_file: core.SaveFile):
    edits.map.edit_chapters(save_file, save_file.gauntlets, "A", base_index=24000)


def edit_collab_gauntlets(save_file: core.SaveFile):
    edits.map.edit_chapters(
        save_file, save_file.collab_gauntlets, "CA", base_index=27000
    )


def edit_behemoth_culling(save_file: core.SaveFile):
    edits.map.edit_chapters(
        save_file, save_file.behemoth_culling, "Q", base_index=31000
    )


def edit_enigma_stages(save_file: core.SaveFile):
    edits.map.edit_chapters(save_file, save_file.enigma_clears, "H", base_index=25000)


def edit_legend_quest(save_file: core.SaveFile):
    edits.map.edit_chapters(save_file, save_file.legend_quest, "D", base_index=16000)


def edit_outbreaks(save_file: core.SaveFile):
    outbreaks = save_file.outbreaks
    chapters = outbreaks.chapters
    if not chapters:
        color.color_print_key("no_valid_outbreaks")
        return

    options = ["clear", "unclear"]
    choice = prompt.choose(prompt.keys(options), dialog="clear_unclear_outbreaks")
    if choice is None:
        return

    clear = choice == 0

    selected_ids = edits.story.select_story_chapters(
        save_file, [chapter.get_true_id() for chapter in chapters.values()]
    )
    if not selected_ids:
        return

    is_per_chapter = edits.story.ask_per_chapter(selected_ids)
    if is_per_chapter is None:
        return
    if is_per_chapter:
        for chapter_id in selected_ids:
            stages = edits.story.select_stages(save_file, chapter_id)
            if not stages:
                continue
            for stage in stages:
                outbreaks.clear_outbreak(chapter_id, stage, clear)
    else:
        stages = edits.story.select_stages(save_file, 0)
        if not stages:
            return
        for stage in stages:
            for chapter_id in selected_ids:
                outbreaks.clear_outbreak(chapter_id, stage, clear)

    if clear:
        color.color_print_key("clear_outbreaks_success")
    else:
        color.color_print_key("unclear_outbreaks_success")


def edit_towers(save_file: core.SaveFile):
    towers = save_file.tower
    edits.map.edit_chapters(save_file, towers.chapters, "V", base_index=7000)


def edit_uncanny(save_file: core.SaveFile):
    uncanny = save_file.uncanny
    edits.map.edit_chapters(save_file, uncanny.chapters, "NA", base_index=13000)


def catamin_clear_count_individual(save_file: core.SaveFile, map_ids: list[int]):
    clear_amount = prompt.number(
        "enter_clear_amount_catamin", max=prompt.MaxValue.i32()
    )
    if clear_amount is None:
        return None
    for map_id in map_ids:
        save_file.event_stages.chapter_completion_count[14_000 + map_id] = clear_amount


def catamin_clear_count_many(
    save_file: core.SaveFile, map_ids: list[int], names: core.MapNames
):
    for map_id in map_ids:
        name = names.map_names.get(map_id) or core.localize(
            "unknown_map_name", id=map_id
        )
        clear_amount = prompt.number(
            "enter_clear_amount_catamin_map",
            max=prompt.MaxValue.i32(),
            name=name,
            id=map_id,
        )
        if clear_amount is None:
            return None
        save_file.event_stages.chapter_completion_count[14_000 + map_id] = clear_amount


def change_clear_amount_catamin(save_file: core.SaveFile):
    names = core.MapNames(save_file, "B", base_index=14000)
    map_ids = edits.map.select_map_names(names.map_names)
    if map_ids is None:
        return None
    if len(map_ids) >= 2:
        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "individual",
                lambda _: catamin_clear_count_individual(save_file, map_ids),
            )
            .add_new_key(
                "all_at_once",
                lambda _: catamin_clear_count_many(save_file, map_ids, names),
            ),
            "catamin_clear_amounts_q",
        )
    else:
        catamin_clear_count_individual(save_file, map_ids)
    color.color_print_key("catamin_stage_success")


def clear_unclear_catamin_stage(save_file: core.SaveFile):
    completed_chapters = edits.map.edit_chapters(
        save_file, save_file.catamin_stages.chapters, "B", base_index=14000
    )
    if completed_chapters is None:
        return None


def edit_catamin_stages(save_file: core.SaveFile):
    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key(
            "change_clear_amount_catamin",
            lambda _: change_clear_amount_catamin(save_file),
        )
        .add_new_key(
            "clear_unclear_stage_catamin",
            lambda _: clear_unclear_catamin_stage(save_file),
        ),
        "catamin_stage_clear_q",
    )


def edit_zero_legends(save_file: core.SaveFile):
    color.color_print_key("zero_legends_warning")
    zero_legends_chapters = save_file.zero_legends
    edits.map.edit_chapters(save_file, zero_legends_chapters, "ND", base_index=34000)


def edit_catclaw_championships(save_file: core.SaveFile):
    zero_legends_chapters = save_file.dojo_chapters
    edits.map.edit_chapters(
        save_file, zero_legends_chapters, "G", base_index=37000, no_r_prefix=True
    )


def edit_dojo_score(save_file: core.SaveFile):
    stage = save_file.dojo.chapters.get_stage(0, 0)
    stage.score = dialog_creator.edit_int_key(
        "dojo_score",
        stage.score,
        prompt.MaxValue.i32().hide_max(),
    )


def edit_challenge_score(save_file: core.SaveFile):
    challenge = save_file.challenge
    if not challenge.scores:
        challenge.scores = [0]
    challenge.scores[0] = dialog_creator.edit_int_key(
        "challenge_score",
        challenge.scores[0],
        prompt.MaxValue.i32().hide_max(),
    )
    challenge.shown_popup = True
    challenge.chapters.clear_stage(0, 0, 0, False)
