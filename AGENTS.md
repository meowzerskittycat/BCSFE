# Agent guide

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor, Gemini and others) working
on this repository. People should start with [README.md](README.md).

BCSFE is a save file editor for The Battle Cats, written in Python. This is a fork of fieryhenry's
editor and is versioned separately (`src/bcsfe/__init__.py`).

## Setup and checks

Python **3.14 or later** is required. The code uses 3.14-only syntax (e.g. `except A, B:`), so
an older interpreter fails to even parse it.

```sh
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pyright                    # strict mode, src only
pytest                     # about 420 tests, a minute or two
pytest --all-answers       # every menu feature with every answer set, a few minutes
```

Run all of these before you commit. CI (`.github/workflows/ci.yml`) runs lint and pyright, then
the tests: on Linux and Windows for pushes to `main`, and on Linux, Windows and macOS with
`--all-answers` for pull requests.

## Hard rules

- **Never commit a real save.** Saves contain the account's inquiry code, password refresh token
  and transfer codes. Real saves go in `tests/saves/` (gitignored). To keep one as a fixture, run
  `python tests/tools/sanitize_save.py path/to/save`, which writes a scrubbed copy to
  `tests/fixtures/real/`.
- **Never send requests to the game's servers** (upload, transfer codes, bans, item packs) while
  testing. Decline upload prompts. These act on a real player's account.
- **Don't commit game data.** `src/bcsfe/files/game_data` and `src/bcsfe/files/map_names` are
  downloaded at run time and gitignored.
- **Don't regenerate the synthetic fixtures** (`tests/tools/gen_fixtures.py`) to make a failing test
  pass. Round-trip tests compare output byte for byte; a change there means the save format
  changed. Fix the code.
- **Don't skip, xfail or loosen a test** to get green.

## Layout

| Path | What it is |
|---|---|
| `src/bcsfe/core/` | The library: reads, edits and writes saves. **Never imports `bcsfe.cli`** (`tests/test_layers.py` checks). It talks to the user only through `core/messages.py` (`show`, `confirm`). |
| `src/bcsfe/core/io/save_layout.py` | The whole save, declared once, in order. Reading, writing, JSON export/import and new saves all come from it. |
| `src/bcsfe/core/io/schema.py` | The declarative field types used by the layout and the sections. |
| `src/bcsfe/core/game/` | Save sections. Stage progress sections share `core/game/map/stage_grid.py`. |
| `src/bcsfe/cli/` | The interactive menu and the command line, built on core. |
| `src/bcsfe/cli/feature_handler.py` | The menu tree. Each key is a locale key; each value is a function taking the `SaveFile`. |
| `src/bcsfe/cli/edits/` | One module per group of menu features. |
| `src/bcsfe/cli/prompt.py` | Every question the editor asks (`text`, `confirm`, `number`, `numbers`, `choose`, `choose_many`). Use these; don't call `input`. |
| `src/bcsfe/cli/commands.py` | The non-interactive `bcsfe <command>` interface. |
| `src/bcsfe/files/locales/` | Messages as `.properties` files, one folder per language (`en`, `vi`, `tw`). |
| `tests/` | `test_roundtrip.py` (byte-identical read/write), `test_features.py` (runs every menu feature), `test_locales.py`, `test_layers.py`, and others. |

## Conventions

- **Messages are locale keys, not strings.** Add English text to `src/bcsfe/files/locales/en/` for
  every key you use; `tests/test_locales.py` fails otherwise. Leave other languages alone (they
  fall back to English) unless you're fixing a broken placeholder. Don't machine-translate.
  See [LOCALIZATION.md](LOCALIZATION.md) for the format.
- **A new menu feature**: write it in `cli/edits/`, add it to the tree in `cli/feature_handler.py`,
  and add its name to the English locale. `test_features.py` will run it automatically.
- **A save format change**: change `save_layout.py` (and the section's schema), then make sure the
  round-trip tests still pass on every fixture. Unknown trailing bytes are kept as
  `remaining_data`; don't guess at fields without real saves that use them.
- **Types**: pyright runs in strict mode. Annotate new code fully.
- **Changelog**: add a line to `CHANGELOG.md` under `[Unreleased]` for anything a user would notice.
- Keep changes small and in the style of the surrounding code. Comments explain why, not what.
