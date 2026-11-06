"""Byte-exact round-trip tests for the save format.

These are the main safety net for refactoring: if any change alters how a
field is read or written, at least one fixture stops round-tripping.
"""

import gzip
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from bcsfe import core

from .conftest import TESTS_DIR, real_fixtures, real_saves, synthetic_saves

sys.path.insert(0, str(TESTS_DIR / "tools"))
import gen_fixtures  # noqa: E402


def assert_round_trips(raw: bytes) -> core.SaveFile:
    save = core.SaveFile(core.Data(raw))
    assert save.to_data().to_bytes() == raw, "binary write differs from input"

    as_dict = save.to_dict()
    from_dict = core.SaveFile.from_dict(as_dict, warn=False)
    assert from_dict.to_dict() == as_dict, "dict round-trip is lossy"
    assert from_dict.to_data().to_bytes() == raw, "save rebuilt from dict differs"
    return save


@pytest.mark.parametrize("path", synthetic_saves(), ids=lambda p: p.stem)
def test_synthetic_round_trip(path: Path) -> None:
    assert_round_trips(path.read_bytes())


@pytest.mark.parametrize("path", synthetic_saves(), ids=lambda p: p.stem)
def test_generator_reproduces_fixture(path: Path) -> None:
    """Building the save from scratch (init_save + from_dict + save) must still
    produce exactly the committed bytes."""
    cc, gv = path.stem.split("_")
    seed = int(gv) * 31 + gen_fixtures.REGIONS.index(cc)
    pinned = set(json.loads(gen_fixtures.PINNED_FILE.read_text()))
    before = set(pinned)
    raw = gen_fixtures.make(cc, int(gv), seed, pinned)
    assert pinned == before, f"new fields needed pinning: {pinned - before}"
    assert raw == path.read_bytes()


@pytest.mark.parametrize("path", synthetic_saves(), ids=lambda p: p.stem)
def test_region_detected_from_hash(path: Path) -> None:
    cc = path.stem.split("_")[0]
    save = core.SaveFile(core.Data(path.read_bytes()))
    assert save.cc.get_code() == cc


@pytest.mark.parametrize("path", real_fixtures(), ids=lambda p: p.name)
def test_real_fixture_round_trip(path: Path) -> None:
    save = assert_round_trips(path.read_bytes())
    cc, gv = path.stem.split("_")
    assert save.cc == core.CountryCode(cc)
    assert save.game_version == core.GameVersion(int(gv))


def test_real_fixtures_hold_no_account_details() -> None:
    for path in real_fixtures():
        save = core.SaveFile(core.Data(path.read_bytes()))
        assert save.inquiry_code == "000000000", path.name
        assert set(save.password_refresh_token) <= {"0"}, path.name
        assert save.transfer_code == save.confirmation_code == "", path.name


JSON_V3_6_0 = sorted((TESTS_DIR / "fixtures" / "json_v3_6_0").glob("*.json.gz"))


@pytest.mark.parametrize("path", JSON_V3_6_0, ids=lambda p: p.name)
def test_json_from_v3_6_0_still_imports(path: Path) -> None:
    """Saves exported to JSON by editor 3.6.0 must import to the same bytes.

    The JSON was written by the code as it was before any schema changes,
    so it catches section rewrites that change key names or value shapes.
    """
    with gzip.open(path, "rt") as f:
        exported = json.load(f)
    save_name = path.name.replace(".json.gz", ".sav")
    raw = next(p for p in synthetic_saves() + real_fixtures() if p.name == save_name)
    imported = core.SaveFile.from_dict(exported, warn=False)
    expected = core.SaveFile(core.Data(raw.read_bytes()))
    # 3.6.0 wrote `ui13` in place of `ui14`, so it read `ui14` back as a copy
    # of `ui13`; that copy is what its JSON holds.
    expected.ui14 = expected.ui13
    assert imported.to_data().to_bytes() == expected.to_data().to_bytes()


@pytest.mark.skipif(not real_saves(), reason="no real saves in tests/saves")
@pytest.mark.parametrize("path", real_saves(), ids=lambda p: p.name)
def test_real_save_round_trip(path: Path) -> None:
    assert_round_trips(path.read_bytes())


def test_corrupted_hash_is_rejected() -> None:
    raw = bytearray(synthetic_saves()[0].read_bytes())
    raw[10] ^= 0xFF
    with pytest.raises(core.CantDetectSaveCCError):
        core.SaveFile(core.Data(bytes(raw)))


def test_truncated_save_reports_offset() -> None:
    raw = synthetic_saves()[-1].read_bytes()
    save = core.SaveFile(core.Data(raw))  # find the region from the intact file
    truncated = core.Data(raw[: len(raw) // 2])
    broken = core.SaveFile(cc=save.cc, load=False)
    broken.data = truncated
    with pytest.raises(core.EndOfDataError, match="offset"):
        broken.load()


def test_layout_change_is_reported_with_marker() -> None:
    data = core.Data()
    data.write_int(110700)
    data.write_int(110800)
    data.reset_pos()
    data.expect_int(110700)
    with pytest.raises(
        core.UnexpectedValueError, match="expected section marker 110900"
    ):
        data.expect_int(110900)


def _string_keyed_dicts(value: Any, path: str, seen: set[int], out: set[str]) -> None:
    if id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, dict):
        if any(isinstance(k, str) and k.lstrip("-").isdigit() for k in value):
            out.add(path)
        for v in value.values():
            _string_keyed_dicts(v, f"{path}[*]", seen, out)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _string_keyed_dicts(v, f"{path}[*]", seen, out)
    elif type(value).__module__.startswith("bcsfe") and hasattr(value, "__dict__"):
        for k, v in vars(value).items():
            if k not in ("data", "save_file"):
                _string_keyed_dicts(v, f"{path}.{k}", seen, out)


@pytest.mark.parametrize(
    "path", real_fixtures() + synthetic_saves()[::8], ids=lambda p: p.name
)
def test_json_import_restores_int_keys(path: Path) -> None:
    """After a trip through real JSON, id-keyed dicts must have int keys again.

    Otherwise editing an id adds a second entry next to the string one and
    the save gets the id written twice.
    """
    save = core.SaveFile(core.Data(path.read_bytes()))
    loaded = core.SaveFile.from_dict(json.loads(json.dumps(save.to_dict())), warn=False)
    found: set[str] = set()
    _string_keyed_dicts(loaded, "save", set(), found)
    assert not found


def test_dojo_json_import_restores_int_keys() -> None:
    """Dojo scores are nested id maps; editing after a JSON import must not
    add a second entry for the same stage."""
    dojo = core.Dojo.deserialize(json.loads(json.dumps({"chapters": {"0": {"0": 5}}})))
    dojo.chapters.get_stage(0, 0).score = 9
    assert dojo.chapters.serialize() == {0: {0: 9}}


@pytest.mark.parametrize("version", [10, 30, 34, 140000])
def test_per_stage_sections_round_trip(version: int) -> None:
    """Item reward and timed score sections share one layout whose header
    depends on the game version."""
    gv = core.GameVersion(version)
    rewards = core.ItemRewardChapters.init(gv)
    scores = core.TimedScoreChapters.init(gv)
    if version >= 34:
        rewards.sub_chapters = [[[True, False, True]] * 2] * 3
        scores.sub_chapters = [[[5, 6, 7]] * 2] * 3
    if version == 34:  # only the map count is stored; stars and stages are fixed
        rewards.sub_chapters = [[[True] * 12] * 3]
        scores.sub_chapters = [[[9] * 12] * 3]
    rewards.item_obtains.item_obtain_sets = {
        2: core.game.map.item_reward_stage.ItemObtainSet({7: True})
    }

    data = core.Data()
    rewards.write(data, gv)
    rewards.write_item_obtains(data)
    scores.write(data, gv)
    data.reset_pos()
    read_rewards = core.ItemRewardChapters.read(data, gv)
    read_rewards.read_item_obtains(data)
    assert read_rewards == rewards
    assert core.TimedScoreChapters.read(data, gv) == scores

    from_json = core.ItemRewardChapters.deserialize(
        json.loads(json.dumps(rewards.serialize()))
    )
    assert from_json == rewards


@pytest.mark.parametrize("version", [90000, 110000, 140200, 150500])
def test_every_number_field_survives_a_round_trip(version: int) -> None:
    """Give each top-level number a value of its own and check it comes back
    from the binary save and from JSON.

    This caught `ui14`, which used to be written as a second copy of `ui13`,
    and `uby21`, which JSON import used to drop.
    """
    from bcsfe.core.io import save_layout
    from bcsfe.core.io.schema import Float, Number

    save = core.SaveFile(
        cc=core.CountryCode("en"), gv=core.GameVersion(version), load=False
    )
    expected: dict[str, int | float] = {}
    for i, e in enumerate(save_layout.fields()):
        if not isinstance(e, save_layout.F) or not e.binary or not e.when(save):
            continue
        if isinstance(e.codec, Number):
            expected[e.name] = 1 + i % 100
        elif isinstance(e.codec, Float):
            expected[e.name] = float(1 + i % 100)
    for name, value in expected.items():
        setattr(save, name, value)

    from_binary = core.SaveFile(save.to_data())
    from_json = core.SaveFile.from_dict(
        json.loads(json.dumps(save.to_dict())), warn=False
    )
    for loaded in (from_binary, from_json):
        got = {name: getattr(loaded, name) for name in expected}
        assert got == expected


def test_save_file_declares_every_layout_field() -> None:
    """`SaveFile`'s annotations give the layout's fields their types; a field
    added to one and not the other would be untyped or never saved."""
    from bcsfe.core.io import save_layout

    declared = list(core.SaveFile.__annotations__)
    assert declared == [e.name for e in save_layout.fields()]
