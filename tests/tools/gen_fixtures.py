"""Generate synthetic save-file fixtures.

Each fixture is a default save for a (region, game version) pair whose
numeric/boolean fields have been filled with deterministic pseudo-random
values. Because almost every field gets a distinct value, a refactor that
reads or writes fields in the wrong order, with the wrong width, or under the
wrong version condition produces different bytes and fails the tests.

Some fields can't take arbitrary values because other parts of the save
depend on them (list lengths, counts, ids). The generator finds those
automatically: it randomizes leaves one prefix at a time and bisects to the
first leaf that breaks a byte-exact round-trip, then pins that leaf
(by path pattern) and tries again.

The fixtures are produced by the *current* code, so they pin today's
behaviour. Regenerate them only on purpose (e.g. when adding support for a
new game version), never to make a failing test pass.

Usage: python tests/tools/gen_fixtures.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from bcsfe import core  # noqa: E402

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "synthetic"
PINNED_FILE = Path(__file__).with_name("pinned_fields.json")

REGIONS = ["en", "jp", "kr", "tw"]
VERSIONS = [
    90000,
    100000,
    110000,
    110500,
    110800,
    111000,
    120000,
    120200,
    120500,
    120700,
    130000,
    130100,
    140000,
    140200,
    140500,
    150300,
    150500,
]

# Top level keys that identify the save rather than hold game state.
KEEP_KEYS = {"editor_version", "cc", "game_version", "dsts", "date", "timestamp"}

Path_ = tuple[Any, ...]


def pattern(path: Path_) -> str:
    """Path with list indices generalised, e.g. story/*/stages/*/clear_times."""
    return "/".join("*" if isinstance(p, int) else str(p) for p in path)


def leaves(value: Any, path: Path_ = ()) -> list[Path_]:
    if isinstance(value, dict):
        out: list[Path_] = []
        for k, v in value.items():  # type: ignore
            if not path and k in KEEP_KEYS:
                continue
            out += leaves(v, path + (k,))
        return out
    if isinstance(value, list):
        out = []
        for i, v in enumerate(value):  # type: ignore
            out += leaves(v, path + (i,))
        return out
    if isinstance(value, (bool, int, float)):
        return [path]
    return []


def random_leaf(value: Any, path: Path_, seed: int) -> Any:
    digest = hashlib.sha256(f"{seed}:{path}".encode()).digest()
    rng = random.Random(digest)
    if isinstance(value, bool):
        return rng.random() < 0.5
    if isinstance(value, int):
        return rng.randint(0, 100)
    if isinstance(value, float):
        return float(rng.randint(0, 1000))
    return value


def set_path(d: Any, path: Path_, value: Any) -> None:
    for p in path[:-1]:
        d = d[p]
    d[path[-1]] = value


def get_path(d: Any, path: Path_) -> Any:
    for p in path:
        d = d[p]
    return d


def build(base: dict[str, Any], paths: list[Path_], seed: int) -> dict[str, Any]:
    d = copy.deepcopy(base)
    for p in paths:
        set_path(d, p, random_leaf(get_path(base, p), p, seed))
    return d


def round_trips(d: dict[str, Any]) -> bytes | None:
    try:
        raw = core.SaveFile.from_dict(copy.deepcopy(d), warn=False).to_data().to_bytes()
        again = core.SaveFile(core.Data(raw)).to_data().to_bytes()
    except Exception:
        return None
    return raw if again == raw else None


def make(cc: str, gv: int, seed: int, pinned: set[str]) -> bytes:
    base = core.SaveFile(
        cc=core.CountryCode(cc), gv=core.GameVersion(gv), load=False
    ).to_dict()
    while True:
        paths = [p for p in leaves(base) if pattern(p) not in pinned]
        raw = round_trips(build(base, paths, seed))
        if raw is not None:
            return raw
        # bisect for the shortest failing prefix; its last leaf is a culprit
        lo, hi = 0, len(paths)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if round_trips(build(base, paths[:mid], seed)) is None:
                hi = mid
            else:
                lo = mid
        culprit = pattern(paths[hi - 1])
        print(f"  pinning {culprit}")
        pinned.add(culprit)


def main() -> None:
    core.core_data.init_data()
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    pinned: set[str] = (
        set(json.loads(PINNED_FILE.read_text())) if PINNED_FILE.exists() else set()
    )
    for cc in REGIONS:
        for gv in VERSIONS:
            raw = make(cc, gv, seed=gv * 31 + REGIONS.index(cc), pinned=pinned)
            path = FIXTURE_DIR / f"{cc}_{gv}.sav"
            path.write_bytes(raw)
            print(f"wrote {path.relative_to(ROOT)} ({len(raw)} bytes)")
            PINNED_FILE.write_text(json.dumps(sorted(pinned), indent=1) + "\n")


if __name__ == "__main__":
    main()
