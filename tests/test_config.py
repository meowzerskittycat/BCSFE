"""A config file that can't be read is replaced, but a copy is kept."""

from pathlib import Path

from bcsfe import core


def test_a_broken_config_is_kept_next_to_the_new_one(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("locale: [unclosed\n")
    config = core.Config(core.Path(str(path)), print_yaml_err=False)
    assert config.get_str(core.ConfigKey.LOCALE) == "en"
    assert (tmp_path / "config.yaml.broken").read_text() == "locale: [unclosed\n"


def test_an_empty_config_leaves_no_copy(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("")
    core.Config(core.Path(str(path)), print_yaml_err=False)
    assert not (tmp_path / "config.yaml.broken").exists()
