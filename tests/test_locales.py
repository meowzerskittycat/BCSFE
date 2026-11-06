"""The editor's messages: every key the code asks for exists, and translations
keep the placeholders the English text has.

A missing key shows its raw name (e.g. `theme_cancelled`) to the user. A
translation that drops `{name}` hides that value; one that adds a `{name}` the
code doesn't pass prints the braces. Untranslated keys are fine: they fall
back to English.
"""

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src" / "bcsfe"
LOCALES = SRC / "files" / "locales"

# Functions whose first argument is a locale key.
KEY_FIRST = {
    "localize",
    "localize_no_alias",
    "get_key",
    "color_print_key",
    "color_input_key",
    "show",
    "confirm",
    "render",
    "text",
    "number",
    "numbers",
}
# Functions whose second argument is (options first, then the question).
KEY_SECOND = {"choose", "choose_many"}

PLACEHOLDER = re.compile(r"(?<!\{)\{([A-Za-z_]\w*)\}(?!\})")
REFERENCE = re.compile(r"\{\{([^{}]+)\}\}")


def load(locale: str) -> dict[str, str]:
    messages: dict[str, str] = {}
    for file in (LOCALES / locale).rglob("*.properties"):
        for line in file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                messages[key.strip()] = value
    return messages


def translations() -> list[str]:
    return sorted(p.name for p in LOCALES.iterdir() if p.is_dir() and p.name != "en")


def keys_in_code() -> dict[str, str]:
    """Literal locale keys passed to the functions above, with where."""
    found: dict[str, str] = {}
    for file in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else None
            if isinstance(func, ast.Name):
                name = func.id
            args: list[ast.expr] = []
            if name in KEY_FIRST:
                args = node.args[:1]
            elif name in KEY_SECOND:
                args = node.args[1:2]
            elif name == "keys" and node.args and isinstance(node.args[0], ast.List):
                args = node.args[0].elts
            for arg in args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    where = f"{file.relative_to(SRC)}:{node.lineno}"
                    found.setdefault(arg.value, where)
    return found


def test_the_scan_finds_keys() -> None:
    assert len(keys_in_code()) > 300


def test_every_key_in_the_code_has_english_text() -> None:
    english = load("en")
    missing = {k: where for k, where in keys_in_code().items() if k not in english}
    assert missing == {}


@pytest.mark.parametrize("locale", ["en", *translations()])
def test_references_point_to_real_keys(locale: str) -> None:
    english, messages = load("en"), load(locale)
    broken = [
        (key, ref)
        for key, value in messages.items()
        for ref in REFERENCE.findall(value)
        if ref not in english and ref not in messages
    ]
    assert broken == []


@pytest.mark.parametrize("locale", translations())
def test_translations_keep_the_placeholders(locale: str) -> None:
    english = load("en")
    wrong = {
        key: (sorted(PLACEHOLDER.findall(english[key])), sorted(PLACEHOLDER.findall(v)))
        for key, v in load(locale).items()
        if key in english
        and set(PLACEHOLDER.findall(v)) != set(PLACEHOLDER.findall(english[key]))
    }
    assert wrong == {}
