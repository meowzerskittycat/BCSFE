"""Strip account details from a real save so it can be committed as a fixture.

Replaces the inquiry code, password refresh token and transfer codes with
placeholders, rewrites the save (which recomputes its hash) and checks the
originals no longer appear anywhere in the output. Game progress is kept.

Usage: python tests/tools/sanitize_save.py SAVE_IN
Writes tests/fixtures/real/{cc}_{game version}.sav
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from bcsfe import core  # noqa: E402

OUT_DIR = ROOT / "tests" / "fixtures" / "real"


def sanitize(raw: bytes) -> tuple[core.SaveFile, bytes]:
    save = core.SaveFile(core.Data(raw))
    secrets = [
        save.inquiry_code,
        save.password_refresh_token,
        save.transfer_code,
        save.confirmation_code,
    ]
    save.inquiry_code = "000000000"
    save.password_refresh_token = "0" * len(save.password_refresh_token)
    save.transfer_code = ""
    save.confirmation_code = ""
    out = save.to_data().to_bytes()
    for secret in secrets:
        if len(secret) >= 6 and secret.encode() in out:
            raise SystemExit("an account detail is still in the output; not writing")
    if core.SaveFile(core.Data(out)).to_data().to_bytes() != out:
        raise SystemExit("sanitized save doesn't round-trip; not writing")
    return save, out


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    core.core_data.init_data()
    save, out = sanitize(Path(sys.argv[1]).read_bytes())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = OUT_DIR / f"{save.cc.get_code()}_{save.game_version.game_version}.sav"
    dst.write_bytes(out)
    print(f"wrote {dst.relative_to(ROOT)} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
