from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from bcsfe.cli import commands

from .conftest import real_fixtures, synthetic_saves


def run(*argv: str) -> int:
    parser = argparse.ArgumentParser()
    commands.add_subcommands(parser)
    return commands.run(parser.parse_args(list(argv)))


def test_info(capsys: pytest.CaptureFixture[str]) -> None:
    assert run("info", str(real_fixtures()[0])) == 0
    out = capsys.readouterr().out
    assert "game version      15.7.0" in out
    assert "region            en" in out


def test_check_passes_on_fixtures(capsys: pytest.CaptureFixture[str]) -> None:
    for path in [real_fixtures()[0], synthetic_saves()[0]]:
        assert run("check", str(path)) == 0
    assert "FAIL" not in capsys.readouterr().out


def test_check_rejects_non_saves(tmp_path: Path) -> None:
    junk = tmp_path / "junk"
    junk.write_bytes(b"not a save" * 10)
    with pytest.raises(SystemExit, match="isn't a Battle Cats save"):
        run("check", str(junk))


def test_export_then_import_gives_the_same_save(tmp_path: Path) -> None:
    save = synthetic_saves()[-1]
    out_json = tmp_path / "save.json"
    out_save = tmp_path / "SAVE_DATA"
    assert run("export", str(save), str(out_json)) == 0
    assert run("import", str(out_json), str(out_save)) == 0
    assert out_save.read_bytes() == save.read_bytes()


def test_import_rejects_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{nope")
    with pytest.raises(SystemExit, match="isn't valid JSON"):
        run("import", str(bad), str(tmp_path / "out"))
