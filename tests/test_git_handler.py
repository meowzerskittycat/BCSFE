"""Git repositories for external locales and themes."""

import pytest

from bcsfe import core
from bcsfe.cli import color
from bcsfe.cli.edits import settings


@pytest.fixture
def git_runs(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Records git commands instead of running them; every clone fails."""
    runs: list[list[str]] = []

    def run(self: core.Command, *_a: object, **_k: object) -> core.CommandResult:
        runs.append(self.args)
        return core.CommandResult.create_failure()

    monkeypatch.setattr(core.Command, "run", run)
    return runs


@pytest.mark.parametrize("url", ["", "/", "https://example.com/x/..", "."])
def test_a_url_without_a_repo_name_is_rejected_before_cloning(
    git_runs: list[list[str]], url: str
) -> None:
    folder = core.GitHandler.get_repo_folder()
    other = folder.add("OtherLocale").add("locale.json")
    other.parent().generate_dirs()
    other.write(core.Data("{}"))

    assert core.GitHandler().get_repo(url, output_error=False) is None
    assert git_runs == []
    assert other.exists()


@pytest.mark.parametrize(
    ("url", "name"),
    [
        ("https://codeberg.org/someone/Locale.git", "Locale.git"),
        ("https://codeberg.org/someone/Locale/", "Locale"),
        ("C:\\locales\\Locale", "Locale"),
    ],
)
def test_repo_name_is_the_last_path_part(url: str, name: str) -> None:
    repo = object.__new__(core.io.git_handler.Repo)
    repo.url = url
    assert repo.get_repo_name() == name


@pytest.mark.parametrize("add", [settings.add_locale, settings.add_theme])
@pytest.mark.parametrize("answer", ["", "q"])
def test_a_blank_repo_cancels_adding(
    monkeypatch: pytest.MonkeyPatch, git_runs: list[list[str]], add: object, answer: str
) -> None:
    monkeypatch.setattr(core.GitHandler, "is_git_installed", staticmethod(lambda: True))
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: answer)
    assert callable(add)
    assert add(core.core_data.config) is None
    assert git_runs == []


def test_a_game_data_repo_without_a_scheme_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    monkeypatch.setattr(
        core.RequestHandler, "get", lambda self, *_a, **_k: sent.append(self.url)
    )
    monkeypatch.setattr(color, "color_input", lambda *_a, **_k: "example.com/bcdata")
    config = core.core_data.config
    before = config.get_str(core.ConfigKey.GAME_DATA_REPO)
    settings.edit_game_data_repo(config)
    assert sent == []
    assert config.get_str(core.ConfigKey.GAME_DATA_REPO) == before
