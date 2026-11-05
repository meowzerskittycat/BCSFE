"""Byte-exact round-trip tests for the save format.

These are the main safety net for refactoring: if any change alters how a
field is read or written, at least one fixture stops round-tripping.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

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
