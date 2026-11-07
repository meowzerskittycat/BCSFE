"""Max several items at once.

Only items the game doesn't treat as purchases are offered. Cat food and rare,
platinum and legend tickets are tracked by the game's servers (the editor
reports them as managed items), so maxing them can get an account banned;
platinum shards turn into platinum tickets. Those are left to their own menu
entries, which warn first. Cats, talents and stages aren't touched either.
"""

from collections.abc import Callable

from bcsfe import core
from bcsfe.cli import color, prompt


def max_xp(save_file: core.SaveFile) -> None:
    save_file.xp = core.core_data.max_value_manager.xp


def max_normal_tickets(save_file: core.SaveFile) -> None:
    save_file.normal_tickets = core.core_data.max_value_manager.normal_tickets


def max_np(save_file: core.SaveFile) -> None:
    save_file.np = core.core_data.max_value_manager.np


def max_leadership(save_file: core.SaveFile) -> None:
    save_file.leadership = core.core_data.max_value_manager.leadership


def max_battle_items(save_file: core.SaveFile) -> None:
    for item in save_file.battle_items.items:
        item.amount = core.core_data.max_value_manager.battle_items


def max_catseyes(save_file: core.SaveFile) -> None:
    value = core.core_data.max_value_manager.catseyes
    save_file.catseyes = [value] * len(save_file.catseyes)


def max_catamins(save_file: core.SaveFile) -> None:
    value = core.core_data.max_value_manager.catamins
    save_file.catamins = [value] * len(save_file.catamins)


def max_catfruit(save_file: core.SaveFile) -> None:
    value = core.core_data.max_value_manager.catfruit_new
    save_file.catfruit = [value] * len(save_file.catfruit)


def max_labyrinth_medals(save_file: core.SaveFile) -> None:
    value = core.core_data.max_value_manager.labyrinth_medals
    save_file.labyrinth_medals = [value] * len(save_file.labyrinth_medals)


def max_treasure_chests(save_file: core.SaveFile) -> None:
    value = core.core_data.max_value_manager.treasure_chests
    save_file.treasure_chests = [value] * len(save_file.treasure_chests)


def options(save_file: core.SaveFile) -> dict[str, Callable[[core.SaveFile], None]]:
    """Locale key -> what maxes it, for the items this save can max safely."""
    items: dict[str, Callable[[core.SaveFile], None]] = {
        "xp": max_xp,
        "normal_tickets": max_normal_tickets,
        "np": max_np,
        "leadership": max_leadership,
        "battle_items": max_battle_items,
        "catseyes": max_catseyes,
        "catamins": max_catamins,
        "catfruit": max_catfruit,
        "labyrinth_medals": max_labyrinth_medals,
        "treasure_chests": max_treasure_chests,
    }
    # Before 11.4 catfruit has one limit shared by every kind, not one each.
    if save_file.game_version < 110400:
        del items["catfruit"]
    return items


def max_all(save_file: core.SaveFile) -> None:
    items = options(save_file)
    keys = list(items)
    color.color_print_key("max_all_note")
    names = [core.localize_no_alias(key) for key in keys]
    picked = prompt.choose_many(names, "max_all_dialog")
    if not picked:
        return
    for i in picked:
        items[keys[i]](save_file)
    color.color_print_key("max_all_done", items=", ".join(names[i] for i in picked))
