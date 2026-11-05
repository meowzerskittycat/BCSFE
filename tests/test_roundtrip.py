"""Byte-exact round-trip tests for the save format.

These are the main safety net for refactoring: if any change alters how a
field is read or written, at least one fixture stops round-tripping.
"""

from __future__ import annotations

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
    assert imported.to_data().to_bytes() == raw.read_bytes()


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
