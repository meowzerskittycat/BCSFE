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

from .conftest import TESTS_DIR, real_saves, synthetic_saves

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


@pytest.mark.skipif(not real_saves(), reason="no real saves in tests/saves")
@pytest.mark.parametrize("path", real_saves(), ids=lambda p: p.name)
def test_real_save_round_trip(path: Path) -> None:
    assert_round_trips(path.read_bytes())


def test_corrupted_hash_is_rejected() -> None:
    raw = bytearray(synthetic_saves()[0].read_bytes())
    raw[10] ^= 0xFF
    with pytest.raises(core.CantDetectSaveCCError):
        core.SaveFile(core.Data(bytes(raw)))
