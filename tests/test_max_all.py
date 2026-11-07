"""Max all only touches items that can't get an account banned."""

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.edits import max_all

from .conftest import real_fixtures

BANNABLE = ("catfood", "rare_tickets", "platinum_tickets", "legend_tickets")


def save() -> core.SaveFile:
    return core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))


def run(monkeypatch: pytest.MonkeyPatch, s: core.SaveFile, answer: str) -> None:
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: answer)
    max_all.max_all(s)


def test_nothing_bannable_is_offered() -> None:
    offered = max_all.options(save())
    for key in (*BANNABLE, "platinum_shards"):
        assert key not in offered


def test_all_maxes_every_item_and_leaves_bannable_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = save()
    before = {key: getattr(s, key) for key in (*BANNABLE, "platinum_shards")}
    run(monkeypatch, s, str(len(max_all.options(s)) + 1))  # the "All" entry

    maxes = core.core_data.max_value_manager
    assert s.xp == maxes.xp
    assert s.np == maxes.np
    assert s.catamins == [maxes.catamins] * len(s.catamins)
    assert s.catseyes == [maxes.catseyes] * len(s.catseyes)
    assert all(item.amount == maxes.battle_items for item in s.battle_items.items)
    for key, value in before.items():
        assert getattr(s, key) == value


def test_only_the_picked_items_change(monkeypatch: pytest.MonkeyPatch) -> None:
    s = save()
    xp, np = s.xp, s.np
    keys = list(max_all.options(s))
    run(monkeypatch, s, str(keys.index("leadership") + 1))
    assert s.leadership == core.core_data.max_value_manager.leadership
    assert (s.xp, s.np) == (xp, np)


def test_catfruit_is_left_out_before_11_4() -> None:
    s = save()
    s.game_version = core.GameVersion(110300)
    assert "catfruit" not in max_all.options(s)
