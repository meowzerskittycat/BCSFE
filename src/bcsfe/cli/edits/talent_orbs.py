from bcsfe import core
from bcsfe.cli import color, dialog_creator, prompt


def color_from_enemy_type(target_id: int | None) -> color.ColorHex:
    if target_id is None:
        return color.ColorHex.WHITE
    if target_id == 0:
        return color.ColorHex.RED
    elif target_id == 1:
        return color.ColorHex.GREEN
    elif target_id == 2:
        return color.ColorHex.DARK_GREY
    elif target_id == 3:
        return color.ColorHex.LIGHT_GREY
    elif target_id == 4:
        return color.ColorHex.YELLOW
    elif target_id == 5:
        return color.ColorHex.BLUE
    elif target_id == 6:
        return color.ColorHex.MAGENTA
    elif target_id == 7:
        return color.ColorHex.DARK_GREEN
    elif target_id == 8:
        return color.ColorHex.WHITE
    elif target_id == 9:
        return color.ColorHex.DARK_MAGENTA
    elif target_id == 10:
        return color.ColorHex.ORANGE
    elif target_id == 11:
        return color.ColorHex.CYAN
    return color.ColorHex.BLACK


def color_from_grade(grade_id: int) -> color.ColorHex:
    if grade_id == 0:
        return color.ColorHex.RED
    elif grade_id == 1:
        return color.ColorHex.ORANGE
    elif grade_id == 2:
        return color.ColorHex.YELLOW
    elif grade_id == 3:
        return color.ColorHex.GREEN
    elif grade_id == 4:
        return color.ColorHex.BLUE
    return color.ColorHex.BLACK


def orb_text(orb: core.OrbInfo) -> str:
    """The orb's description, coloured by target, grade and effect."""
    raw = orb.raw_orb_info
    target_color = color_from_enemy_type(raw.target_id).value
    rank_color = color_from_grade(raw.rank_id).value
    effect_text = orb.effect.replace("%@", "{}")
    effect_text = f"<@t>{effect_text}</>"
    return effect_text.format(
        f"<{rank_color}>{orb.rank}</>",
        f"<{target_color}>{orb.target}</>" if orb.target else "",
    )


class SaveOrbs:
    def __init__(
        self,
        orbs: dict[int, core.SaveOrb],
        orb_info_list: core.OrbInfoList,
    ):
        """Initialize the SaveOrbs class

        Args:
            orbs (dict[int, core.SaveOrb]): The orbs
            orb_info_list (core.OrbInfoList): The orb info list
        """
        self.orbs = orbs
        self.orb_info_list = orb_info_list

    @staticmethod
    def from_save_file(save_file: core.SaveFile) -> SaveOrbs | None:
        """Create a SaveOrbs from the save stats

        Args:
            save_file (core.SaveFile): The save file

        Returns:
            SaveOrbs | None: The SaveOrbs
        """
        orb_info_list = core.OrbInfoList.create(save_file)
        if orb_info_list is None:
            return None
        orbs: dict[int, core.SaveOrb] = {}
        for orb_id, orb in save_file.talent_orbs.orbs.items():
            try:
                orb_info = orb_info_list.orb_info_list[int(orb_id)]
            except IndexError:
                orb_info = core.OrbInfo.create_unknown(int(orb_id))
            orbs[int(orb_id)] = core.SaveOrb(orb_info, orb.value)

        return SaveOrbs(orbs, orb_info_list)

    def print(self):
        """Print the orbs as a formatted list"""
        self.sort_orbs()
        total_orbs = sum([orb.count for orb in self.orbs.values()])
        color.color_print_key("total_current_orbs", total_orbs=total_orbs)
        color.color_print_key("total_current_orb_types", total_types=len(self.orbs))
        color.color_print_key("current_orbs")
        for orb in self.orbs.values():
            color.color_print(f"<@q>{orb.count}</> {orb_text(orb.orb)}")

    def sort_orbs(self):
        """Sort the orbs by attribute, effect, grade and id in that order with attribute being the most important"""
        orbs = list(self.orbs.values())
        orbs.sort(key=lambda orb: orb.orb.raw_orb_info.orb_id)
        orbs.sort(key=lambda orb: orb.orb.raw_orb_info.rank_id)
        orbs.sort(key=lambda orb: orb.orb.raw_orb_info.effect_id)
        orbs.sort(key=lambda orb: orb.orb.raw_orb_info.target_id or -1)

    def localize_attribute(self, attribute: str | None) -> str | None:
        if attribute is not None:
            return attribute

    def edit_ind(self, orb_selection: list[core.OrbInfo], max_orbs: int):
        for orb in orb_selection:
            orb_id = orb.raw_orb_info.orb_id
            try:
                orb_count = self.orbs[orb_id].count
            except KeyError:
                orb_count = 0

            orb_count = dialog_creator.edit_int_raw(
                orb_text(orb), orb_count, prompt.MaxValue.i16(max_orbs)
            )

            self.orbs[orb_id] = core.SaveOrb(orb, orb_count)

    def edit_many(self, max_orbs: int, orb_selection: list[core.OrbInfo]):
        orb_count = prompt.number(
            "edit_orbs_all", max=prompt.MaxValue.i16(max_orbs), escape=False
        )
        if orb_count is None:
            return
        orb_count = prompt.MaxValue.specific(max_orbs, 16).clamp(orb_count)
        for orb in orb_selection:
            orb_id = orb.raw_orb_info.orb_id
            self.orbs[orb_id] = core.SaveOrb(orb, orb_count)

    def edit(self):
        """Edit the orbs"""
        # this code sucks quit a lot, but it works and i can't be bothered making it better atm
        self.print()
        all_grades = self.orb_info_list.get_all_grades()
        all_grades = [grade for grade in all_grades]
        all_grades.sort()
        all_attributes = self.orb_info_list.get_all_attributes()
        all_attributes = [
            self.localize_attribute(attribute) or ""
            for attribute in all_attributes
            if attribute
        ]
        all_attributes.sort()
        all_effects = self.orb_info_list.get_all_effects()
        all_effects.sort()
        all_effects_str = [
            effect.lower().replace("%@", "").replace(":", "").strip() + f" <@s>({i})</>"
            for (i, effect) in enumerate(all_effects)
        ]
        all_effect_ids = [i for i in range(len(all_effects))]

        all_grades_str = ",".join(
            f"<{color_from_grade(self.orb_info_list.get_all_grades().index(grade))}>{grade}</>"
            for grade in all_grades
        )

        all_attributes_str = ",".join(
            f"<{color_from_enemy_type(self.orb_info_list.get_all_attributes().index(attribute))}>{attribute}</>"
            for attribute in all_attributes
        )

        all_effects_str = ", ".join(
            f"<@t>{effect_str}</>" for effect_str in all_effects_str
        )

        color.color_print_key(
            "edit_orbs_help",
            escape=False,
            all_grades_str=all_grades_str,
            all_attributes_str=all_attributes_str,
            all_effects_str=all_effects_str,
        )

        orb_input_selection = (
            color.color_input_key("orb_select")
            .lower()
            .replace("angle", "angel")
            .split(",")
        )
        if orb_input_selection == [core.core_data.local_manager.get_key("quit_key")]:
            return

        orb_selection: list[core.OrbInfo] = []

        for orb_input in orb_input_selection:
            grade = None
            attribute = None
            effect = None
            orb_input = orb_input.strip()
            parts = orb_input.split(" ")
            parts = [part.lower() for part in parts if part != ""]
            if len(parts) == 0:
                continue
            if parts[0] == "*":
                orb_selection = self.orb_info_list.orb_info_list
                break
            for available_grade in all_grades:
                if available_grade.lower() in parts:
                    grade = available_grade
                    break
            for available_attribute in all_attributes:
                if available_attribute.lower() in parts:
                    attribute = available_attribute
                    break
            for available_effect in all_effect_ids:
                if str(available_effect) in parts:
                    effect = all_effects[available_effect]
                    break
            if grade is None:
                grade = "*"
            if attribute is None:
                attribute = "*"
            if effect is None:
                effect = "*"
            orbs = self.orb_info_list.get_orbs_from_component_fuzzy(
                grade, attribute, effect
            )
            orb_selection.extend(orbs)

        orb_selection = list(set(orb_selection))
        orb_selection.sort(key=lambda orb: orb.raw_orb_info.orb_id)
        orb_selection.sort(key=lambda orb: orb.raw_orb_info.rank_id)
        orb_selection.sort(key=lambda orb: orb.raw_orb_info.effect_id)
        orb_selection.sort(key=lambda orb: orb.raw_orb_info.target_id or -1)

        color.color_print_key("selected_orbs")

        for orb in orb_selection:
            color.color_print(orb_text(orb))

        max_orbs = core.core_data.max_value_manager.talent_orbs

        if len(orb_selection) == 0:
            return
        if len(orb_selection) == 1:
            self.edit_ind(orb_selection, max_orbs)
        else:
            dialog_creator.single_select_key(
                dialog_creator.Actions[None]
                .new()
                .add_new_key(
                    "individual", lambda _: self.edit_ind(orb_selection, max_orbs)
                )
                .add_new_key(
                    "edit_all_at_once",
                    lambda _: self.edit_many(max_orbs, orb_selection),
                ),
                "edit_orbs_individually",
            )

        self.print()

    def save(self, save_file: core.SaveFile):
        """Save the orbs to the save_stats

        Args:
            save_file (core.SaveFile): The save_stats to save the orbs to
        """
        for orb_id, orb in self.orbs.items():
            save_file.talent_orbs.orbs[orb_id] = core.TalentOrb(orb_id, orb.count)

    @staticmethod
    def edit_talent_orbs(save_file: core.SaveFile):
        """Edit the talent orbs

        Args:
            save_file (core.SaveFile): The save_stats to edit the orbs of

        """
        save_orbs = SaveOrbs.from_save_file(save_file)
        if save_orbs is None:
            color.color_print_key("failed_to_load_orbs")
            return None
        save_orbs.edit()
        save_orbs.save(save_file)
