"""Non-interactive commands, for scripts and for checking saves quickly.

    bcsfe info SAVE            summary of a save
    bcsfe check SAVE           verify the editor reads and writes it unchanged
    bcsfe export SAVE OUT      save -> JSON
    bcsfe import JSON OUT      JSON -> save

Output is plain English text, so it's easy to paste into bug reports.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from bcsfe import __version__, core


def add_subcommands(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("info", help="print a summary of a save file")
    p.add_argument("save", type=Path)

    p = sub.add_parser(
        "check",
        help="check the editor can read and re-write a save without changing it",
    )
    p.add_argument("save", type=Path)

    p = sub.add_parser("export", help="convert a save file to JSON")
    p.add_argument("save", type=Path)
    p.add_argument("out", type=Path, help="JSON file to write ('-' for stdout)")

    p = sub.add_parser("import", help="convert JSON back into a save file")
    p.add_argument("json", type=Path)
    p.add_argument("out", type=Path, help="save file to write")


def run(args: argparse.Namespace) -> int:
    try:
        if args.command == "info":
            return info(args.save)
        if args.command == "check":
            return check(args.save)
        if args.command == "export":
            return export(args.save, args.out)
        if args.command == "import":
            return import_json(args.json, args.out)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    raise ValueError(f"unknown command {args.command!r}")


def load(path: Path) -> core.SaveFile:
    raw = path.read_bytes()
    try:
        return core.SaveFile(core.Data(raw))
    except core.CantDetectSaveCCError:
        raise SystemExit(
            f"error: {path} isn't a Battle Cats save, or it has been modified "
            "without updating its hash"
        ) from None
    except core.DataError as e:
        raise SystemExit(f"error: couldn't parse {path}: {e}") from None


def info(path: Path) -> int:
    save = load(path)
    unlocked = sum(1 for cat in save.cats.cats if cat.unlocked)
    rows: list[tuple[str, Any]] = [
        ("region", save.cc.get_code()),
        ("game version", save.game_version.to_string()),
        ("inquiry code", save.inquiry_code or "(none)"),
        ("cat food", save.catfood),
        ("xp", save.xp),
        ("np", save.np),
        ("rare tickets", save.rare_tickets),
        ("platinum tickets", save.platinum_tickets),
        ("legend tickets", save.legend_tickets),
        ("cats unlocked", f"{unlocked} / {len(save.cats.cats)}"),
        ("user rank", save.calculate_user_rank()),
    ]
    width = max(len(name) for name, _ in rows)
    for name, value in rows:
        print(f"{name.ljust(width)}  {value}")
    return 0


def check(path: Path) -> int:
    raw = path.read_bytes()
    save = load(path)
    print(
        f"read {path} ({len(raw)} bytes, {save.cc.get_code()} "
        f"{save.game_version.to_string()})"
    )
    ok = True

    out = save.to_data().to_bytes()
    if out == raw:
        print("ok: writing it back gives identical bytes")
    else:
        ok = False
        at = next(
            (i for i, (a, b) in enumerate(zip(raw, out, strict=False)) if a != b),
            min(len(raw), len(out)),
        )
        print(f"FAIL: re-written save differs from offset {at}")

    try:
        again = core.SaveFile.from_dict(save.to_dict(), warn=False)
        if again.to_data().to_bytes() == raw:
            print("ok: exporting to JSON and importing again gives identical bytes")
        else:
            ok = False
            print("FAIL: JSON export/import changes the save")
    except Exception as e:  # report, don't crash: this is a diagnostic
        ok = False
        print(f"FAIL: JSON export/import raised {type(e).__name__}: {e}")

    if save.remaining_data:
        print(
            f"note: {len(save.remaining_data)} bytes at the end aren't parsed yet "
            "(newer game data); they are kept unchanged"
        )
    return 0 if ok else 1


def export(path: Path, out: Path) -> int:
    data = load(path).to_dict()
    text = json.dumps(data, indent=4)
    if str(out) == "-":
        print(text)
    else:
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)
    return 0


def import_json(path: Path, out: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise SystemExit(f"error: {path} isn't valid JSON: {e}") from None
    editor_version = data.get("editor_version")
    if editor_version not in (None, __version__):
        print(
            f"warning: JSON was exported by editor {editor_version}, "
            f"this is {__version__}",
            file=sys.stderr,
        )
    try:
        save = core.SaveFile.from_dict(data, warn=False)
        raw = save.to_data().to_bytes()
    except (core.SaveError, KeyError, TypeError, ValueError) as e:
        raise SystemExit(f"error: couldn't build a save from {path}: {e}") from None
    out.write_bytes(raw)
    print(f"wrote {out} ({len(raw)} bytes)", file=sys.stderr)
    return 0
