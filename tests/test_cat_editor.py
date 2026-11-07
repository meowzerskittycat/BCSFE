"""Picking cats from a gacha banner by name."""

import pytest

from bcsfe import core
from bcsfe.cli import prompt
from bcsfe.cli.edits import cat_editor

from .conftest import real_fixtures


class FakeBanners:
    def __init__(self, _save_file: core.SaveFile) -> None:
        pass

    def get_all_names(self) -> dict[int, str]:
        return {9: "Second", 5: "First"}


def test_banners_are_listed_with_their_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    shown: list[str] = []

    def choose_many(options: list[str], *_a: object, **_k: object) -> list[int]:
        shown.extend(options)
        return [1]

    monkeypatch.setattr(core, "GatyaInfos", FakeBanners)
    monkeypatch.setattr(prompt, "confirm", lambda *_a, **_k: False)
    monkeypatch.setattr(prompt, "choose_many", choose_many)

    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    picked = cat_editor.CatEditor(save).select_gatya_banner_name()

    assert picked == [9]
    assert [
        core.core_data.local_manager.get_key("banner_txt", name=n, int=i)
        for i, n in ((5, "First"), (9, "Second"))
    ] == shown
    assert not any("{int}" in option for option in shown)
