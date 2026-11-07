"""A theme the config names but that can't be read falls back to the default."""

from bcsfe import core


def test_a_missing_theme_uses_the_default() -> None:
    default = core.ThemeHandler("default").theme_data
    assert default.get("colors")
    assert core.ThemeHandler("no-such-theme").theme_data == default
