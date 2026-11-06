"""The rules every question follows (see `bcsfe.cli.prompt`)."""

from collections.abc import Callable
from typing import Any

import pytest

from bcsfe.cli import color, prompt


def ask[T](
    monkeypatch: pytest.MonkeyPatch, answers: list[str], question: Callable[[], T]
) -> tuple[T, list[str]]:
    """Run `question` with typed `answers`; return its result and the keys of
    any messages it printed."""
    typed = iter(answers)
    printed: list[str] = []
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: next(typed))
    monkeypatch.setattr(color, "color_print", lambda *_a, **_k: None)

    def record(key: str, *_a: Any, **_k: Any) -> None:
        printed.append(key)

    monkeypatch.setattr(color, "color_print_key", record)
    result = question()
    assert next(typed, None) is None, "not every answer was used"
    return result, printed


Q = prompt.Raw("?")
OPTIONS = ["Cats", "Rare Tickets", "Cat Food"]


@pytest.mark.parametrize("answer", ["", "q", "  q  "])
def test_nothing_or_q_cancels_every_question(monkeypatch, answer: str) -> None:
    for question in (
        lambda: prompt.confirm(Q),
        lambda: prompt.numbers(Q, max=10),
        lambda: prompt.choose(OPTIONS, Q),
        lambda: prompt.choose_many(OPTIONS, Q),
        lambda: prompt.number(Q, max=10),
    ):
        assert ask(monkeypatch, [answer], question)[0] is None


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("3", [3]),
        ("1 3", [1, 3]),
        ("2-4", [2, 3, 4]),
        ("all", [0, 1, 2, 3, 4, 5]),  # includes the maximum
        ("ALL", [0, 1, 2, 3, 4, 5]),
    ],
)
def test_numbers(monkeypatch, answer: str, expected: list[int]) -> None:
    assert ask(monkeypatch, [answer], lambda: prompt.numbers(Q, max=5))[0] == expected


@pytest.mark.parametrize("bad", ["6", "1 x", "4-2", "1-", "-1"])
def test_bad_numbers_are_asked_again_not_dropped(monkeypatch, bad: str) -> None:
    result, printed = ask(monkeypatch, [bad, "1"], lambda: prompt.numbers(Q, max=5))
    assert result == [1]
    assert printed


def test_confirm(monkeypatch) -> None:
    assert ask(monkeypatch, ["y"], lambda: prompt.confirm(Q))[0] is True
    assert ask(monkeypatch, ["No"], lambda: prompt.confirm(Q))[0] is False
    result, printed = ask(monkeypatch, ["1", "yes"], lambda: prompt.confirm(Q))
    assert result is True
    assert printed == ["invalid_yes_no"]


def test_choose_by_number_or_name(monkeypatch) -> None:
    assert ask(monkeypatch, ["2"], lambda: prompt.choose(OPTIONS, Q))[0] == 1
    assert ask(monkeypatch, ["cat food"], lambda: prompt.choose(OPTIONS, Q))[0] == 2
    result, printed = ask(
        monkeypatch, ["1 2", "dog", "4", "1"], lambda: prompt.choose(OPTIONS, Q)
    )
    assert result == 0
    assert len(printed) == 3


def test_choose_many(monkeypatch) -> None:
    def many(answer: str) -> list[int] | None:
        return ask(monkeypatch, [answer], lambda: prompt.choose_many(OPTIONS, Q))[0]

    assert many("3 1 3") == [2, 0]
    assert many("1-2") == [0, 1]
    assert many("4") == [0, 1, 2]  # the "All" entry
    assert many("all") == [0, 1, 2]
    assert many("rare tickets") == [1]


def test_single_option_is_picked_without_asking(monkeypatch) -> None:
    assert ask(monkeypatch, [], lambda: prompt.choose(["Only"], Q))[0] == 0
    assert ask(monkeypatch, [], lambda: prompt.choose_many(["Only"], Q))[0] == [0]


def test_number(monkeypatch) -> None:
    assert ask(monkeypatch, [""], lambda: prompt.number(Q, max=9, default=4))[0] == 4
    result, printed = ask(
        monkeypatch, ["x", "10", "9"], lambda: prompt.number(Q, max=9)
    )
    assert result == 9
    assert printed == ["invalid_input_int", "invalid_input_int"]
    assert ask(monkeypatch, ["50"], lambda: prompt.number(Q, max=9, clamp=True))[0] == 9
    assert ask(monkeypatch, ["-5"], lambda: prompt.number(Q, max=9, clamp=True))[0] == 0


def test_text_keeps_a_literal_q(monkeypatch) -> None:
    assert ask(monkeypatch, ["hello"], lambda: prompt.text(Q))[0] == "hello"
    assert ask(monkeypatch, ["q"], lambda: prompt.text(Q))[0] is None
    assert ask(monkeypatch, ["\\q"], lambda: prompt.text(Q))[0] == "q"
