import argparse
import subprocess
import sys
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


def test_export_to_a_closed_pipe_is_quiet() -> None:
    """`bcsfe export SAVE - | head` shouldn't print a broken pipe error."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "bcsfe", "export", str(real_fixtures()[0]), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None and proc.stderr is not None
    assert proc.stdout.read(10).startswith(b"{")
    proc.stdout.close()
    err = proc.stderr.read().decode()
    proc.wait(timeout=60)
    assert "Broken pipe" not in err and "Traceback" not in err


def test_import_rejects_bad_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{nope")
    with pytest.raises(SystemExit, match="isn't valid JSON"):
        run("import", str(bad), str(tmp_path / "out"))


def edited_copy(tmp_path: Path) -> Path:
    from bcsfe import core

    save = core.SaveFile(core.Data(real_fixtures()[0].read_bytes()))
    save.xp += 1000
    save.cats.cats[5].unlocked = 1 - save.cats.cats[5].unlocked
    save.inquiry_code = "abcdef123"
    out = tmp_path / "edited"
    out.write_bytes(save.to_data().to_bytes())
    return out


def test_diff_of_identical_saves(capsys: pytest.CaptureFixture[str]) -> None:
    path = str(real_fixtures()[0])
    assert run("diff", path, path) == 0
    assert "no differences" in capsys.readouterr().out


def test_diff_lists_each_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("diff", str(real_fixtures()[0]), str(edited_copy(tmp_path))) == 1
    out = capsys.readouterr().out
    assert "xp: " in out
    assert "cats.cats[5].unlocked: " in out
    assert "3 changes in 3 sections" in out
    assert "editor_version" not in out


def test_diff_hides_account_credentials(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run("diff", str(real_fixtures()[0]), str(edited_copy(tmp_path)))
    out = capsys.readouterr().out
    assert "inquiry_code: changed (hidden)" in out
    assert "abcdef123" not in out


def test_diff_limit_still_counts_everything(
    capsys: pytest.CaptureFixture[str],
) -> None:
    saves = synthetic_saves()
    assert run("diff", str(saves[0]), str(saves[-1]), "--limit", "3") == 1
    out = capsys.readouterr().out
    listed = [line for line in out.splitlines() if ": " in line and "->" in line]
    assert len(listed) == 3
    assert "more (use --limit 0 for all)" in out
    assert "more sections" in out


def test_compare_reports_length_and_added_keys() -> None:
    changes: list[tuple[str, str]] = []
    commands.compare({"a": [1, 2], "b": 1}, {"a": [1, 3, 4], "c": 2}, "", changes)
    assert changes == [
        ("a[1]", "2 -> 3"),
        ("a", "length 2 -> 3"),
        ("b", "removed"),
        ("c", "added"),
    ]
