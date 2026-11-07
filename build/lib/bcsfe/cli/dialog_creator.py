from collections.abc import Callable
from typing import Any

from bcsfe import core
from bcsfe.cli import color, prompt
from bcsfe.cli.prompt import MaxValue


type ActionFunc[T] = Callable[[int], T]


class NoAssignedActionException(Exception):
    def __init__(self, index: int):
        super().__init__(f"No assigned action to index {index}")


class Action[T]:
    def __init__(self, options: list[str], func: ActionFunc[T]):
        self.options = options
        self.func = func

    def len(self) -> int:
        return len(self.options)

    @staticmethod
    def new_raw(options: str | list[str], func: ActionFunc[T]) -> Action[T]:
        if isinstance(options, str):
            options = [options]
        return Action(options, func)

    @staticmethod
    def new_key(
        options: str | list[str],
        func: ActionFunc[T],
        escape: bool = True,
        **kwargs: Any,
    ) -> Action[T]:
        if isinstance(options, str):
            options = [options]

        options_ls = [core.localize(opt, escape, **kwargs) for opt in options]

        return Action[T].new_raw(options_ls, func)

    def run(self, index: int) -> T:
        return self.func(index)


class Actions[T]:
    def __init__(self, actions: list[Action[T]]):
        self.actions = actions

    def len(self) -> int:
        return len(self.actions)

    def is_empty(self) -> bool:
        return self.len() == 0

    @staticmethod
    def new() -> Actions[T]:
        return Actions([])

    def add(self, action: Action[T]) -> Actions[T]:
        self.actions.append(action)

        return self

    def add_new_raw(self, options: str | list[str], func: ActionFunc[T]) -> Actions[T]:
        return self.add(Action[T].new_raw(options, func))

    def add_new_key(
        self,
        options: str | list[str],
        func: ActionFunc[T],
        escape: bool = True,
        **kwargs: Any,
    ) -> Actions[T]:
        return self.add(Action[T].new_key(options, func, escape, **kwargs))

    def get(self, index: int) -> Action[T] | None:
        current = 0
        for action in self.actions:
            if current >= index:
                return action
            current += action.len()
        return None

    def get_rebase(self, index: int) -> tuple[Action[T], int] | None:
        current = 0
        for action in self.actions:
            if index < current + action.len():
                return action, index - current
            current += action.len()
        return None

    def max(self) -> int:
        current = 0
        for action in self.actions:
            current += action.len()
        return current

    def run(self, index: int) -> T:
        action = self.get(index)
        if action is None:
            raise NoAssignedActionException(index)

        return action.run(index)

    def to_string(self) -> str:
        lines: list[str] = []

        i = 1
        for action in self.actions:
            for opt in action.options:
                lines.append(f" {i}. <@t>{opt}</>")
                i += 1

        return "\n".join(lines)

    def display(self):
        color.color_print(self.to_string())


def single_select_key[T](
    actions: Actions[T],
    dialog_key: str,
    escape: bool = True,
    **kwargs: Any,
) -> T | None:
    """Show every action's options; run the action whose option is picked."""
    options = [opt for action in actions.actions for opt in action.options]
    picked = prompt.choose(options, dialog_key, escape, **kwargs)
    if picked is None:
        return None
    action = actions.get_rebase(picked)
    if action is None:
        return None
    return action[0].run(action[1])


def edit_int_raw(item_name: str, current_value: int, max: MaxValue) -> int:
    if max.show:
        key = "input"
    else:
        key = "input_no_max"

    dialog = core.localize(
        key, name=item_name, value=current_value, max=max.max, escape=False
    )

    val = prompt.number(prompt.Raw(dialog), max=max, clamp=True)
    if val is None or val == current_value:
        color.color_print_key(
            "value_unchanged", name=item_name, value=current_value, escape=False
        )
        return current_value
    color.color_print_key("value_changed", name=item_name, value=val, escape=False)
    return val


def edit_str_raw(item_name: str, current_value: str) -> str:
    dialog = core.localize("input_no_max", name=item_name, value=current_value)

    val = prompt.text(prompt.Raw(dialog))
    if not val or val == current_value:
        color.color_print_key("value_unchanged", name=item_name, value=current_value)
        return current_value
    color.color_print_key("value_changed", name=item_name, value=val)
    return val


def edit_int_key(
    item_key: str,
    current_value: int,
    max: MaxValue,
    escape: bool = True,
    **kwargs: Any,
) -> int:
    return edit_int_raw(core.localize(item_key, escape, **kwargs), current_value, max)


def edit_str_key(
    item_key: str,
    current_value: str,
    escape: bool = True,
    **kwargs: Any,
) -> str:
    return edit_str_raw(core.localize(item_key, escape, **kwargs), current_value)


class CumulativeMax:
    def __init__(self, max: MaxValue):
        self.max = max

    @staticmethod
    def specific(max: int, bits: int) -> CumulativeMax:
        return CumulativeMax(MaxValue.specific(max, bits))

    @staticmethod
    def new(max: MaxValue):
        return CumulativeMax(max)

    def get(self, current_values: list[int], ids: list[int] | int) -> MaxValue:
        if isinstance(ids, int):
            ids = [ids]

        v = 0
        for id in ids:
            v += current_values[id]

        return MaxValue.specific(self.max.max - sum(current_values) + v, self.max.bits)


class MultiMax:
    def __init__(self, maxes: list[MaxValue]):
        self.maxes = maxes

    @staticmethod
    def new(maxes: list[MaxValue]) -> MultiMax:
        return MultiMax(maxes)

    def get(self, id: int) -> MaxValue | None:
        if id < 0 or id >= len(self.maxes):
            return None
        return self.maxes[id]

    def maximal(self, ids: list[int]) -> MaxValue:
        m = MaxValue.specific(0, 0)
        for id in ids:
            m_v = self.get(id)
            if m_v is None:
                continue
            if m_v.max > m.max:
                m = m_v

        return m


def edit_ints_key(
    group_name: str,
    item_names: list[str],
    current_values: list[int],
    max: MultiMax | CumulativeMax | MaxValue,
    escape: bool = True,
    **kwargs: Any,
) -> list[int]:
    return edit_ints_raw(
        core.localize(group_name, escape, **kwargs), item_names, current_values, max
    )


def edit_ints_raw(
    group_name: str,
    item_names: list[str],
    current_values: list[int],
    max: MultiMax | CumulativeMax | MaxValue,
) -> list[int]:
    entries = prompt.choose_many(
        [
            core.localize("value", name=name, value=value)
            for name, value in zip(item_names, current_values, strict=False)
        ],
        "input_many",
        min=1,
        max=len(item_names) + 1,
    )

    if not entries:
        return current_values

    if len(entries) == 1:
        edit_individual(current_values, max, entries, item_names)
        return current_values

    single_select_key(
        Actions[None]
        .new()
        .add_new_key(
            "individually",
            lambda _: edit_individual(current_values, max, entries, item_names),
        )
        .add_new_key(
            "edit_all_at_once",
            lambda _: edit_many(current_values, max, entries, group_name, item_names),
        ),
        "individual_or_all_at_once",
        group=group_name,
    )

    return current_values


def edit_individual(
    current_values: list[int],
    max: MaxValue | MultiMax | CumulativeMax,
    entries: list[int],
    names: list[str],
):
    entries_c = entries.copy()
    for id in entries:
        if isinstance(max, MultiMax):
            _max = max.get(id)
            if _max is None:
                return
        elif isinstance(max, CumulativeMax):
            _max = max.get(current_values, entries_c)
        else:
            _max = max
        new_val = edit_int_raw(names[id], current_values[id], _max)
        current_values[id] = new_val
        entries_c.pop(0)


def edit_many(
    current_values: list[int],
    max: MaxValue | MultiMax | CumulativeMax,
    entries: list[int],
    group_name: str,
    names: list[str],
):
    if isinstance(max, MultiMax):
        _max = max.maximal(entries)
    elif isinstance(max, CumulativeMax):
        _max = MaxValue.specific(
            max.get(current_values, entries).max // len(entries), max.max.bits
        )
    else:
        _max = max
    val = prompt.number("input_generic", max=_max, clamp=True, name=group_name)
    if val is None:
        return

    for id in entries:
        if isinstance(max, MultiMax):
            maxm = max.get(id)
            if maxm is None:
                continue
            _max = maxm
        val_ = _max.clamp(val)
        current_values[id] = val_
        color.color_print_key("value_changed", name=names[id], value=val_, escape=False)
