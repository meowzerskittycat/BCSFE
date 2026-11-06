"""Every question the editor asks, with one set of rules.

- Nothing, or the quit key (`q`), cancels: the function returns `None`.
  When editing a value, cancelling keeps the current value.
- An answer that can't be used is explained and the question is asked again;
  parts of it are never silently dropped.
- Lists of numbers take spaces, ranges (`1-5`) and `all`. Choosing from
  options also takes an option's name.
- Ctrl+C (or closed input) raises KeyboardInterrupt, as everywhere else.

`dialog` arguments are locale keys, formatted with the keyword arguments.
Wrap text in `Raw` to show it as it is.
"""

from typing import Any

from bcsfe import core
from bcsfe.cli import color


class Raw(str):
    """Text shown as it is instead of being looked up as a locale key."""


def render(dialog: str, escape: bool = True, **kwargs: Any) -> str:
    if isinstance(dialog, Raw):
        return str(dialog)
    return core.localize(dialog, escape, **kwargs)


def _quit_key() -> str:
    return core.localize("quit_key")


def _answer(text: str) -> str | None:
    """The stripped answer, or None for nothing or the quit key."""
    answer = color.color_input(text).strip()
    if not answer or answer == _quit_key():
        return None
    return answer


# --- text and yes/no ------------------------------------------------------


def text(dialog: str, escape: bool = True, **kwargs: Any) -> str | None:
    """Free text. Typing `\\q` gives a literal `q`."""
    answer = color.color_input(render(dialog, escape, **kwargs))
    if answer.strip() == _quit_key():
        return None
    if answer == f"\\{_quit_key()}":
        return _quit_key()
    return answer


def confirm(dialog: str, escape: bool = False, **kwargs: Any) -> bool | None:
    """Yes or no; asks again for anything else."""
    question = render(dialog, escape, **kwargs)
    yes = {core.localize("yes_key").lower(), "yes"}
    no = {core.localize("no_key").lower(), "no"}
    while True:
        answer = _answer(question)
        if answer is None:
            return None
        if answer.lower() in yes:
            return True
        if answer.lower() in no:
            return False
        color.color_print_key("invalid_yes_no")


# --- numbers --------------------------------------------------------------


def number(
    dialog: str,
    *,
    min: int = 0,
    max: int,
    default: int | None = None,
    clamp: bool = False,
    escape: bool = True,
    **kwargs: Any,
) -> int | None:
    """A whole number from `min` to `max`. Nothing gives `default`."""
    question = render(dialog, escape, **kwargs)
    while True:
        answer = color.color_input(question).strip()
        if not answer:
            return default
        if answer == _quit_key():
            return None
        try:
            value = int(answer)
        except ValueError:
            color.color_print_key("invalid_input_int", min=min, max=max)
            continue
        if min <= value <= max:
            return value
        if clamp:
            return max if value > max else min
        color.color_print_key("invalid_input_int", min=min, max=max)


def parse_numbers(
    answer: str, *, min: int, max: int, names: list[str] | None = None
) -> list[int] | None:
    """Numbers, ranges, `all`, or (with `names`) one option's name, from
    `min` to `max` inclusive. Prints why and returns None if any part is bad.

    With `names`, `min` is the number of the first name.
    """
    if answer.lower() == core.localize("all").lower():
        return list(range(min, max + 1))
    if names and answer.strip(" -0123456789"):
        lowered = answer.lower()
        for i, name in enumerate(names):
            if name.lower().strip() == lowered:
                return [min + i]
        color.color_print_key("invalid_input_int", min=min, max=max)
        return None
    values: list[int] = []
    for part in answer.split():
        low, sep, high = part.partition("-")
        if not low.isdigit() or (sep and not high.isdigit()):
            color.color_print_key("invalid_range", val=part)
            return None
        start, end = int(low), int(high) if sep else int(low)
        if end < start:
            color.color_print_key("invalid_range", val=part)
            return None
        if start < min or end > max:
            color.color_print_key("invalid_input_int", min=min, max=max)
            return None
        values.extend(range(start, end + 1))
    return values


def numbers(
    dialog: str, *, min: int = 0, max: int, escape: bool = True, **kwargs: Any
) -> list[int] | None:
    """Several whole numbers from `min` to `max` (e.g. ids)."""
    question = render(dialog, escape, **kwargs)
    while True:
        answer = _answer(question)
        if answer is None:
            return None
        values = parse_numbers(answer, min=min, max=max)
        if values is not None:
            return values


# --- choosing from options ------------------------------------------------


def show_options(options: list[str], extra: list[str] | None = None) -> None:
    lines = [f" {i}. <@t>{opt}</>" for i, opt in enumerate(options + (extra or []), 1)]
    color.color_print("\n".join(lines))


def choose(
    options: list[str], dialog: str, escape: bool = True, **kwargs: Any
) -> int | None:
    """The index of one option, picked by number or name. A single option is
    picked without asking."""
    if not options:
        return None
    if len(options) == 1:
        return 0
    question = render(dialog, escape, **kwargs)
    while True:
        show_options(options)
        answer = _answer(question)
        if answer is None:
            return None
        picked = parse_numbers(answer, min=1, max=len(options), names=options)
        if picked is not None and len(picked) == 1:
            return picked[0] - 1
        if picked is not None:
            color.color_print_key("choose_one")


def choose_many(
    options: list[str], dialog: str, escape: bool = True, **kwargs: Any
) -> list[int] | None:
    """The indexes of the options picked, in the order typed (duplicates
    removed). A single option is picked without asking."""
    if not options:
        return None
    if len(options) == 1:
        return [0]
    question = render(dialog, escape, **kwargs)
    every = core.localize("all")
    while True:
        show_options(options, [every])
        answer = _answer(question)
        if answer is None:
            return None
        picked = parse_numbers(answer, min=1, max=len(options) + 1, names=options)
        if picked is None:
            continue
        if len(options) + 1 in picked:  # the "All" entry
            return list(range(len(options)))
        return list(dict.fromkeys(i - 1 for i in picked))
