import sys

import pytest

from bcsfe import core


def test_arguments_are_not_shell_split(tmp_path):
    weird = tmp_path / "dir with spaces; echo injected"
    weird.mkdir()
    code = "import sys; print(sys.argv[1])"
    result = core.Command([sys.executable, "-c", code, str(weird)]).run()
    assert result.success
    assert result.result.strip() == str(weird)


def test_missing_program_fails_like_a_shell():
    result = core.Command(["definitely-not-a-real-program-bcsfe"]).run()
    assert result.exit_code == 127
    assert not result.success


def test_shell_strings_are_rejected():
    with pytest.raises(TypeError):
        core.Command("echo hi")  # type: ignore[arg-type]


def test_path_run_passes_arguments():
    result = core.Path(sys.executable).run("-c", "print('ok')")
    assert result.result.strip() == "ok"
