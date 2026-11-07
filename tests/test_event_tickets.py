"""Editing event tickets changes the ticket that was picked."""

from types import SimpleNamespace

import pytest

from bcsfe import core
from bcsfe.cli import dialog_creator
from bcsfe.cli.edits import event_tickets

from .conftest import real_fixtures

EVENT = core.GatyaItemCategory.EVENT_TICKETS.value


def ticket_event(number: int) -> SimpleNamespace:
    when = SimpleNamespace(
        start_yyyymmdd=20260101, start_hhmm=0, end_yyyymmdd=20260102, end_hhmm=0
    )
    return SimpleNamespace(
        sets=[SimpleNamespace(number=number, message="")],
        filter=when,
        get_normal_flag=lambda: True,
        get_rare_flag=lambda: False,
        get_collab_flag=lambda: False,
    )


def fake_init(tickets: event_tickets.EventTickets, save: core.SaveFile) -> None:
    # Ticket 100 has no slot in the save; ticket 200 is slot 0.
    items = {
        100: SimpleNamespace(id=100, category=EVENT, index=10_000),
        200: SimpleNamespace(id=200, category=EVENT, index=0),
    }
    options = {
        1: SimpleNamespace(ticket_item_id=100),
        2: SimpleNamespace(ticket_item_id=200),
    }
    tickets.save_file = save
    tickets.gatya_item_buy = items  # type: ignore[assignment]
    tickets.gatya_item_names = SimpleNamespace(get_name=lambda _id: None)  # type: ignore[assignment]
    tickets.gatya_option_n = options  # type: ignore[assignment]
    tickets.gatya_option_r = {}  # type: ignore[assignment]
    tickets.gatya_option_e = {}  # type: ignore[assignment]
    tickets.gatya_event_data = SimpleNamespace(items=[ticket_event(1), ticket_event(2)])  # type: ignore[assignment]


def test_the_shown_ticket_is_the_one_edited(monkeypatch: pytest.MonkeyPatch) -> None:
    shown: list[str] = []

    def edit(_key: str, names: list[str], values: list[int], **_k: object) -> list[int]:
        shown.extend(names)
        return [v + 5 for v in values]

    monkeypatch.setattr(event_tickets.EventTickets, "__init__", fake_init)
    monkeypatch.setattr(dialog_creator, "edit_ints_key", edit)

    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    before = save.event_capsules[0]
    event_tickets.EventTickets.edit(save)

    assert len(shown) == 1
    assert save.event_capsules[0] == before + 5
