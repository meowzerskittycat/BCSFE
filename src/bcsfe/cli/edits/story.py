import random

from bcsfe import core
from bcsfe.cli import color, dialog_creator, edits, prompt


def select_story_chapters(
    save_file: core.SaveFile, chapters: list[int] | None = None
) -> list[int] | None:
    chapter_names = core.StoryChapters.get_chapter_names(save_file, chapters)

    if chapter_names is None:
        return None

    selected_chapters = prompt.choose_many(chapter_names, "select_story_chapters")

    return selected_chapters


def get_selected_chapter_progress(max_stages: int = 48) -> int | None:
    progress = prompt.number(
        "edit_chapter_progress_all",
        min=0,
        max=prompt.MaxValue.always_cap(max_stages),
    )
    if progress is None:
        return None

    return progress


def edit_chapter_progress(
    save_file: core.SaveFile,
    chapter_id: int,
    chapter_name: str,
    clear_amount: int,
    clear_amount_choose: int,
) -> bool:
    max_stages = 48
    chapter = save_file.story.get_real_chapters()[chapter_id]
    progress = prompt.number(
        "edit_chapter_progress",
        min=0,
        max=prompt.MaxValue.always_cap(max_stages),
        chapter_name=chapter_name,
    )
    if progress is None:
        return False
    clear_amounts = [1] * progress
    if clear_amount_choose == 0:
        clear_amount2 = edits.map.ask_clear_amount()
        if clear_amount2 is None:
            return False
        clear_amounts = [clear_amount2] * progress
    elif clear_amount_choose == 1:
        clear_amounts = [clear_amount] * progress
    elif clear_amount_choose == 2:
        for i in range(progress):
            print_current_stage(save_file, chapter_id, i)
            clear_amount2 = edits.map.ask_clear_amount()
            if clear_amount2 is None:
                return False
            clear_amounts[i] = clear_amount2

    chapter.apply_progress(progress, clear_amounts)
    return progress != 0


def ask_clear_count() -> int | None:
    clear_count = prompt.number(
        "edit_stage_clear_count",
        min=0,
        max=prompt.MaxValue.i16(core.core_data.max_value_manager.stage_clear_count),
    )

    return clear_count


def ask_if_individual_clear_counts() -> bool | None:
    return dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("individual_clear_counts", lambda _: True)
        .add_new_key("all_clear_counts", lambda _: False),
        "individual_clear_counts_dialog",
    )


def edit_stage_clear_count(save_file: core.SaveFile, chapter_id: int, stage_id: int):
    chapter = save_file.story.get_real_chapters()[chapter_id]
    stage = chapter.stages[stage_id]
    clear_count = ask_clear_count()
    if clear_count is None:
        return
    stage.clear_times = clear_count


def print_current_chapter(save_file: core.SaveFile, chapter_id: int):
    chapter_names = core.StoryChapters.get_chapter_names(save_file)
    if chapter_names is None:
        return
    chapter_name = chapter_names[chapter_id]
    color.color_print_key("current_chapter", chapter_name=chapter_name)


def print_current_treasure_group(
    save_file: core.SaveFile, chapter_id: int, treasure_group_id: int
):
    chapter_type = core.StoryChapters.get_chapter_type_from_index(chapter_id)

    treasure_group_names = core.game.map.story.TreasureGroupNames(
        save_file, chapter_type
    ).treasure_group_names
    if treasure_group_names is None:
        return
    treasure_group_name = treasure_group_names[treasure_group_id]
    color.color_print_key(
        "current_treasure_group", treasure_group_name=treasure_group_name
    )


def clear_story(save_file: core.SaveFile):
    story = save_file.story
    edit_chapters(
        story,
        save_file,
    )


def edit_chapters(story: core.StoryChapters, save_file: core.SaveFile):
    chapters = story.get_real_chapters()
    names = core.StoryChapters.get_chapter_names(save_file)
    if names is None:
        return

    map_choices = select_story_chapters(save_file)
    if not map_choices:
        return

    clear_type_choice = prompt.choose(
        prompt.keys(["clear_whole_chapters", "clear_specific_stages"]),
        dialog="select_clear_type",
    )
    if clear_type_choice is None:
        return

    modify_clear_amounts = prompt.confirm("modify_clear_amounts")
    if modify_clear_amounts is None:
        return
    clear_amount = 1
    clear_amount_type = -1
    if modify_clear_amounts:
        if len(map_choices) == 1:
            clear_amount_type = 0
        else:
            options = ["clear_amount_chapter", "clear_amount_all"]
            if clear_type_choice == 1:
                options.append("clear_amount_stages")
            clear_amount_type = prompt.choose(
                prompt.keys(options), dialog="select_clear_amount_type"
            )
            if clear_amount_type is None:
                return

        if clear_amount_type == 1:
            clear_amount = edits.map.ask_clear_amount()
            if clear_amount is None:
                return

    for id in map_choices:
        stage_names = core.StageNames(
            save_file, chapter=str(story.get_chapter_type_from_index(id))
        )
        stage_names = stage_names.stage_names
        if stage_names is None:
            return

        new_stage_names: list[str] = []
        for i in range(48):
            index_stage_id = core.StoryChapters.convert_stage_id(i)
            new_stage_names.append(stage_names[index_stage_id])
        stage_names = new_stage_names
        map_name = names[id]
        color.color_print_key("current_sol_chapter", name=map_name, id=id)
        if clear_type_choice:
            stages = edits.map.ask_stages_stage_names(stage_names)
            if stages is None:
                return
        else:
            stages = list(range(48))

        if clear_amount_type == 0:
            clear_amount = edits.map.ask_clear_amount()
            if clear_amount is None:
                return

        could_unclear_stages = False

        if chapters[id].progress > max(stages) + 1:
            could_unclear_stages = True

        for stage in range(max(stages) + 1, 48):
            if chapters[id].stages[stage].clear_times:
                could_unclear_stages = True

        if could_unclear_stages:
            unclear_other_stages = prompt.confirm("unclear_other_stages")
            if unclear_other_stages is None:
                return
        else:
            unclear_other_stages = False

        if unclear_other_stages:
            chapters[id].progress = 0
            for stage in range(max(stages), 48):
                chapters[id].stages[stage].clear_times = 0

        for stage in stages:
            if clear_amount_type == 2:
                stage_name = stage_names[stage]
                color.color_print_key("current_sol_stage", name=stage_name, id=stage)
            if clear_amount_type == 2:
                clear_amount = edits.map.ask_clear_amount()
                if clear_amount is None:
                    return
            story.clear_stage(
                id,
                stage,
                overwrite_clear_progress=True,
                clear_amount=clear_amount,
                chapters=chapters,
            )

    color.color_print_key("map_chapters_edited")


def custom_treasure_level() -> int | None:
    max_treasure_level = core.core_data.max_value_manager.treasure_level
    treasure_level = prompt.number(
        "custom_treasure_level_dialog",
        min=0,
        max=prompt.MaxValue.i32(max_treasure_level),
    )
    if treasure_level is None:
        return None
    return treasure_level


def ask_treasure_level(save_file: core.SaveFile) -> int | None:
    treasure_text = core.core_data.get_treasure_text(save_file).treasure_text
    if treasure_text is None:
        return None

    return dialog_creator.single_select_key(
        dialog_creator.Actions[int | None]
        .new()
        .add_new_key("no_treasure", lambda _: 0)
        .add_new_raw(treasure_text[:3], lambda v: v + 1)
        .add_new_key("custom_treasure_level", lambda _: custom_treasure_level()),
        "treasure_level_dialog",
    )


def ask_per_chapter(chapters: list[int]) -> bool | None:
    if len(chapters) == 1:
        return True

    return dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("per_chapter", lambda _: True)
        .add_new_key("all_selected_chapters", lambda _: False),
        "edit_per_chapter",
    )


def edit_treasures_whole_chapters(save_file: core.SaveFile, chapters: list[int]):
    is_per_chapter = ask_per_chapter(chapters)
    if is_per_chapter is None:
        return

    if is_per_chapter:
        for chapter_id in chapters:
            print_current_chapter(save_file, chapter_id)
            chapter = save_file.story.get_real_chapters()[chapter_id]
            treasure_level = ask_treasure_level(save_file)
            if treasure_level is None:
                return
            for stage in chapter.get_valid_treasure_stages():
                stage.set_treasure(treasure_level)
    else:
        treasure_level = ask_treasure_level(save_file)
        if treasure_level is None:
            return
        for chapter_id in chapters:
            chapter = save_file.story.get_real_chapters()[chapter_id]
            for stage in chapter.get_valid_treasure_stages():
                stage.set_treasure(treasure_level)


def select_stages_by_id() -> list[int] | None:
    stage_ids = prompt.numbers("select_stage_id", min=1, max=48)
    if stage_ids is None:
        return None
    stage_ids = [stage_id - 1 for stage_id in stage_ids]
    return stage_ids


def select_stage_by_name(save_file: core.SaveFile, chapter_id: int) -> list[int] | None:
    chapter_type = core.StoryChapters.get_chapter_type_from_index(chapter_id)
    stage_names = core.StageNames(save_file, str(chapter_type)).stage_names
    if not stage_names:
        return None
    new_stage_names: list[str] = []
    for i in range(48):
        index_stage_id = core.StoryChapters.convert_stage_id(i)
        new_stage_names.append(stage_names[index_stage_id])
    selected_stages = prompt.choose_many(new_stage_names, dialog="select_stages_name")

    if not selected_stages:
        return None

    return selected_stages


def select_stages(save_file: core.SaveFile, chapter_id: int) -> list[int] | None:
    return dialog_creator.single_select_key(
        dialog_creator.Actions[list[int] | None]
        .new()
        .add_new_key("select_stage_by_id", lambda _: select_stages_by_id())
        .add_new_key(
            "select_stage_by_name",
            lambda _: select_stage_by_name(save_file, chapter_id),
        ),
        "select_stage_dialog",
    )


def edit_treasures_individual_stages(save_file: core.SaveFile, chapters: list[int]):
    is_per_chapter = ask_per_chapter(chapters)
    if is_per_chapter is None:
        return
    if is_per_chapter:
        for chapter_id in chapters:
            print_current_chapter(save_file, chapter_id)
            chapter = save_file.story.get_real_chapters()[chapter_id]
            stage_ids = select_stages(save_file, chapter_id)
            if stage_ids is None:
                return
            treasure_level = ask_treasure_level(save_file)
            if treasure_level is None:
                return
            for stage_id in stage_ids:
                real_stage_id = core.StoryChapters.convert_stage_id(stage_id)
                chapter.set_treasure(real_stage_id, treasure_level)
    else:
        stage_ids = select_stages(save_file, 0)
        if stage_ids is None:
            return
        treasure_level = ask_treasure_level(save_file)
        if treasure_level is None:
            return
        for chapter_id in chapters:
            chapter = save_file.story.get_real_chapters()[chapter_id]
            for stage_id in stage_ids:
                real_stage_id = core.StoryChapters.convert_stage_id(stage_id)
                chapter.set_treasure(real_stage_id, treasure_level)


def edit_treasure_group_ind(
    save_file: core.SaveFile,
    chapter_id: int,
    treasure_group_data: list[list[int]],
    chapter: core.game.map.story.Chapter,
    selected_treasure_groups: list[int],
):
    for treasure_group_id in selected_treasure_groups:
        print_current_treasure_group(save_file, chapter_id, treasure_group_id)
        treasure_level = ask_treasure_level(save_file)
        if treasure_level is None:
            return
        treasure_group = treasure_group_data[treasure_group_id]
        for stage_id in treasure_group:
            chapter.set_treasure(stage_id, treasure_level)


def edit_treasure_group_many(
    save_file: core.SaveFile,
    treasure_group_data: list[list[int]],
    chapter: core.game.map.story.Chapter,
    selected_treasure_groups: list[int],
):
    treasure_level = ask_treasure_level(save_file)
    if treasure_level is None:
        return

    for treasure_group_id in selected_treasure_groups:
        treasure_group = treasure_group_data[treasure_group_id]
        for stage_id in treasure_group:
            chapter.set_treasure(stage_id, treasure_level)


def edit_treasures_groups(save_file: core.SaveFile, chapters: list[int]):
    for chapter_id in chapters:
        print_current_chapter(save_file, chapter_id)
        chapter = save_file.story.get_real_chapters()[chapter_id]
        chapter_type = core.StoryChapters.get_chapter_type_from_index(chapter_id)
        treasure_group_data = core.game.map.story.TreasureGroupData(
            save_file, chapter_type
        ).treasure_group_data
        treasure_group_names = core.game.map.story.TreasureGroupNames(
            save_file, chapter_type
        ).treasure_group_names
        if treasure_group_data is None or treasure_group_names is None:
            return
        treasure_group_names_new: list[str] = []
        for i in range(len(treasure_group_data)):
            treasure_group_names_new.append(treasure_group_names[i])

        selected_treasure_groups = prompt.choose_many(
            treasure_group_names_new, dialog="select_treasure_groups"
        )

        if selected_treasure_groups is None:
            return

        dialog_creator.single_select_key(
            dialog_creator.Actions[None]
            .new()
            .add_new_key(
                "group_individual",
                lambda _: edit_treasure_group_ind(
                    save_file,
                    chapter_id,
                    treasure_group_data,  # type: ignore
                    chapter,
                    selected_treasure_groups,  # type: ignore
                ),
            )
            .add_new_key(
                "group_all_at_once",
                lambda _: edit_treasure_group_many(
                    save_file,
                    treasure_group_data,  # type: ignore
                    chapter,
                    selected_treasure_groups,  # type: ignore
                ),
            ),
            "select_treasure_groups_individual",
        )


def edit_treasures(save_file: core.SaveFile):
    selected_chapters = select_story_chapters(save_file)
    if not selected_chapters:
        return
    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key(
            "whole_chapters",
            lambda _: edit_treasures_whole_chapters(save_file, selected_chapters),
        )
        .add_new_key(
            "individual_stages",
            lambda _: edit_treasures_individual_stages(save_file, selected_chapters),
        )
        .add_new_key(
            "treasure_groups",
            lambda _: edit_treasures_groups(save_file, selected_chapters),
        ),
        "treasure_dialog",
    )

    color.color_print_key("treasures_edited")


def edit_itf_timed_scores(save_file: core.SaveFile):
    selected_chapters = select_story_chapters(save_file, chapters=[3, 4, 5])
    if not selected_chapters:
        return
    selected_chapters = [chapter_id + 3 for chapter_id in selected_chapters]
    dialog_creator.single_select_key(
        dialog_creator.Actions[None]
        .new()
        .add_new_key(
            "whole_chapters",
            lambda _: edit_itf_timed_scores_whole_chapters(
                save_file, selected_chapters
            ),
        )
        .add_new_key(
            "individual_stages",
            lambda _: edit_itf_timed_scores_individual_stages(
                save_file, selected_chapters
            ),
        ),
        "itf_timed_scores_dialog",
    )

    color.color_print_key("itf_timed_scores_edited")


def itf_timed_score_input() -> tuple[int, int] | None:
    inp = prompt.text("itf_timed_score_dialog")
    if inp is None:
        return None

    parts = inp.split("-", maxsplit=1)

    parts_i: list[int] = []
    for part in parts:
        if not part.isdigit():
            return itf_timed_score_input()
        score = int(part)
        mx = prompt.MaxValue.i32(core.core_data.max_value_manager.itf_timed_score)
        score = mx.clamp(score)
        parts_i.append(score)

    return min(parts_i), max(parts_i) + 1


def edit_itf_timed_scores_whole_chapters(save_file: core.SaveFile, chapters: list[int]):
    is_per_chapter = ask_per_chapter(chapters)
    if is_per_chapter is None:
        return

    if is_per_chapter:
        for chapter_id in chapters:
            print_current_chapter(save_file, chapter_id)
            chapter = save_file.story.get_real_chapters()[chapter_id]
            score = itf_timed_score_input()
            if score is None:
                return
            for stage in chapter.get_valid_treasure_stages():
                stage.itf_timed_score = random.randrange(score[0], score[1])
    else:
        score = itf_timed_score_input()
        if score is None:
            return
        for chapter_id in chapters:
            chapter = save_file.story.get_real_chapters()[chapter_id]
            for stage in chapter.get_valid_treasure_stages():
                stage.itf_timed_score = random.randrange(score[0], score[1])


def print_current_stage(save_file: core.SaveFile, chapter_id: int, stage_id: int):
    chapter_names = core.StoryChapters.get_chapter_names(save_file)
    if chapter_names is None:
        return
    chapter_name = chapter_names[chapter_id]
    chapter_type = core.StoryChapters.get_chapter_type_from_index(chapter_id)
    stage_names = core.StageNames(save_file, str(chapter_type)).stage_names
    if stage_names is None:
        return
    stage_id = core.StoryChapters.convert_stage_id(stage_id)
    stage_name = stage_names[stage_id]
    color.color_print_key(
        "current_stage", chapter_name=chapter_name, stage_name=stage_name
    )


def edit_itf_timed_scores_ind_per_chapter_ind(
    save_file: core.SaveFile,
    chapter: core.game.map.story.Chapter,
    chapter_id: int,
    stage_ids: list[int],
):
    for stage_id in stage_ids:
        print_current_stage(save_file, chapter_id, stage_id)

        score = itf_timed_score_input()

        if score is None:
            return
        chapter.stages[stage_id].itf_timed_score = random.randrange(score[0], score[1])


def edit_itf_timed_scores_ind_per_chapter_many(
    chapter: core.game.map.story.Chapter, stage_ids: list[int]
):
    score = itf_timed_score_input()
    if score is None:
        return
    for stage_id in stage_ids:
        chapter.stages[stage_id].itf_timed_score = random.randrange(score[0], score[1])


def edit_itf_timed_scores_ind_per_chapter(
    save_file: core.SaveFile, chapters: list[int], is_ind: bool
):
    for chapter_id in chapters:
        print_current_chapter(save_file, chapter_id)
        chapter = save_file.story.get_real_chapters()[chapter_id]
        stage_ids = select_stages(save_file, chapter_id)
        if stage_ids is None:
            return
        if is_ind:
            edit_itf_timed_scores_ind_per_chapter_ind(
                save_file, chapter, chapter_id, stage_ids
            )
        else:
            edit_itf_timed_scores_ind_per_chapter_many(chapter, stage_ids)


def edit_itf_timed_scores_ind_many(
    save_file: core.SaveFile, chapters: list[int], is_ind: bool
):
    stage_ids = select_stages(save_file, 3)
    if stage_ids is None:
        return
    if is_ind:
        for stage_id in stage_ids:
            print_current_stage(save_file, 3, stage_id)
            score = itf_timed_score_input()
            if score is None:
                return
            for chapter_id in chapters:
                chapter = save_file.story.get_real_chapters()[chapter_id]
                chapter.stages[stage_id].itf_timed_score = random.randrange(
                    score[0], score[1]
                )
    else:
        score = itf_timed_score_input()
        if score is None:
            return
        for chapter_id in chapters:
            chapter = save_file.story.get_real_chapters()[chapter_id]
            for stage_id in stage_ids:
                chapter.stages[stage_id].itf_timed_score = random.randrange(
                    score[0], score[1]
                )


def edit_itf_timed_scores_individual_stages(
    save_file: core.SaveFile, chapters: list[int]
):
    is_per_chapter = ask_per_chapter(chapters)
    if is_per_chapter is None:
        return
    is_ind = dialog_creator.single_select_key(
        dialog_creator.Actions[bool]
        .new()
        .add_new_key("individual_stages", lambda _: True)
        .add_new_key("all_selected_stages", lambda _: False),
        "itf_timed_scores_individual_dialog",
    )
    if is_ind is None:
        return

    if is_per_chapter:
        edit_itf_timed_scores_ind_per_chapter(save_file, chapters, is_ind)
    else:
        edit_itf_timed_scores_ind_many(save_file, chapters, is_ind)
