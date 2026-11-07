"""Core shows messages and asks questions through the CLI it is connected to."""

from typing import Any

import bcsfe.cli  # noqa: F401  (importing the CLI connects it)
from bcsfe import core
from bcsfe.cli import color


def test_core_messages_are_shown_by_the_cli(monkeypatch) -> None:
    shown: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        color, "color_print_key", lambda key, **kw: shown.append((key, kw))
    )
    core.messages.show("no_internet")
    assert shown == [("no_internet", {"escape": True})]


def test_core_questions_are_asked_by_the_cli(monkeypatch) -> None:
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: "y")
    assert core.messages.confirm("do_you_want_to_continue") is True
