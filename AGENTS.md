# Agent guide

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor, Gemini and others) working
on this repository. People should start with [README.md](README.md). Keep this file accurate: when
you change something it describes, update it in the same commit.

## What this is

BCSFE is a save file editor for The Battle Cats, written in Python. It reads a save, lets the user
edit it from an interactive menu (or a few non-interactive commands), and writes it back
byte-for-byte compatible with the game.

This repository (`meowzerskittycat/BCSFE` on GitHub) is a **fork** of fieryhenry's BCSFE-Python
(now on Codeberg). It has its own version line, `4.x` (`src/bcsfe/__init__.py`), and upstream's
PyPI package `bcsfe` is **not** this fork: `pip install bcsfe` installs upstream. This fork is
installed from git, and the editor's **Check for updates** follows this repository's `main`.

## Setup and checks

Python **3.14 or later** is required. The code uses 3.14-only syntax (e.g. `except A, B:` without
parentheses), so an older interpreter can't even parse it. Check `python --version` first.

```sh
pip install -e ".[dev]"
python tests/tools/get_game_data.py   # game data for the menu tests (gitignored)
ruff check src tests
ruff format --check src tests
pyright                    # strict mode, src only
pytest                     # about 580 tests, a minute or two
pytest --all-answers       # every menu feature with every answer set (about 940 tests, about five minutes)
pytest --cov               # with coverage; fails below fail_under in pyproject.toml
pytest tests/test_locales.py   # just the message checks
```

Run all of these before you commit, and `--all-answers` too if you touched a menu feature, a
prompt or the config. CI (`.github/workflows/ci.yml`) runs lint and pyright, then the tests:

- pull requests: Linux, Windows and macOS, with `--all-answers`;
- pushes to `main`: Linux and Windows only (macOS runners queue for a long time and a job left
  waiting is cancelled, which used to turn `main`'s badge red with no test failing);
- newer pushes to a pull request cancel its older run;
- the Linux job measures branch coverage and fails if it drops below `fail_under`
  (`pyproject.toml`); the report is in the run's summary. Raise the floor as tests are added;
  never lower it to get green.
- Dependabot (`.github/dependabot.yml`) opens one weekly PR bumping the workflows' actions. It
  doesn't watch Python packages: they have no upper bounds, so CI always tests the latest.

## Hard rules

- **Never commit a real save, or anything derived from one that isn't sanitized.** Saves contain
  the account's inquiry code, password refresh token and transfer codes. Real saves go in
  `tests/saves/` (gitignored). To keep one as a fixture, run
  `python tests/tools/sanitize_save.py path/to/save`, which writes a scrubbed copy to
  `tests/fixtures/real/`. Don't paste save contents, inquiry codes or tokens into commits, issues or
  PR text either.
- **Never contact the game's servers** (uploading a save, transfer codes, unbanning, item packs,
  inquiry codes) while developing or testing, unless the user explicitly asks. These act on a
  real player's account. Decline upload prompts when driving the editor.
- **Don't commit game data.** `src/bcsfe/files/game_data` and `src/bcsfe/files/map_names` are
  downloaded at run time and gitignored.
- **Don't regenerate the synthetic fixtures** (`tests/tools/gen_fixtures.py`) to make a failing test
  pass. They pin the current save format byte for byte; if a round-trip test fails, the code
  changed the format. Regenerate only on purpose (e.g. support for a new game version), and say so.
- **Don't skip, xfail or loosen a test** to get green.
- **Keep the translations complete.** When you add or change an English message, add or update
  the Vietnamese (`vi`) and Traditional Chinese (`tw`) one in the same commit; translate it
  yourself. `tests/test_locales.py` fails if either is missing a message or has an empty one. Use
  the terms each file already uses: `vi` keeps game names in English (Cat Food, Rare Tickets,
  save, backup), `tw` uses the Taiwanese game's names (貓罐頭, 稀有券, 存檔, 備份). Keep every
  `{placeholder}`, `{{reference}}` and colour tag. The `vi` files use CRLF line endings: edit them
  with `open(..., newline="")` so they stay that way.
- **Don't install the package from a local `git+file://` URL** to test updates. It once spawned
  thousands of git processes and exhausted memory. Test the updater with the mocks in
  `tests/test_cli.py`.

## Layout

| Path | What it is |
|---|---|
| `src/bcsfe/__main__.py` | Entry point (`bcsfe`, `python -m bcsfe`): argument parsing, then the menu or a command. |
| `src/bcsfe/core/` | The library: reads, edits and writes saves. **Never imports `bcsfe.cli`** (`tests/test_layers.py` checks). It talks to the user only through `core/messages.py` (`show`, `confirm`), which the CLI connects when imported. |
| `src/bcsfe/core/io/save_layout.py` | The whole save, declared once, in order. Reading, writing, JSON export/import and new saves all come from it. |
| `src/bcsfe/core/io/schema.py` | The declarative field types (`F`, `I32`, `Map`, `Rest`, `group`, `ge(...)`) the layout and sections use. |
| `src/bcsfe/core/io/save.py` | `SaveFile`: load, save, checksum, JSON. |
| `src/bcsfe/core/io/config.py` | Settings (`ConfigKey`), stored as YAML in the user's config folder. |
| `src/bcsfe/core/game/` | Save sections (cats, items, stages, gamatoto, ...). Stage progress sections share `core/game/map/stage_grid.py`. |
| `src/bcsfe/core/server/` | Talking to the game's servers, and `updater.py` (updates from this fork's GitHub). |
| `src/bcsfe/core/locale_handler.py` | `LocalManager`: loads the locale files. `core.localize()` (in `core/__init__.py`) looks messages up. |
| `src/bcsfe/cli/` | The interactive menu and the command line, built on core. |
| `src/bcsfe/cli/feature_handler.py` | The menu tree. Each key is a locale key; each value is a function that takes the `SaveFile`. Also search and undo. |
| `src/bcsfe/cli/edits/` | One module per group of menu features. `settings.py` is the config editor. |
| `src/bcsfe/cli/prompt.py` | Every question the editor asks (`text`, `confirm`, `number`, `numbers`, `choose`, `choose_many`). Use these, never `input()`. |
| `src/bcsfe/cli/commands.py` | Non-interactive `bcsfe info / export / import ...`. |
| `src/bcsfe/files/` | Bundled data: `locales/` (`en`, `vi`, `tw`), `themes/`, etc. |
| `tests/conftest.py` | Points the editor at a temporary data and config folder, so tests never touch the user's files. |
| `tests/fixtures/` | `synthetic/` (generated saves for every region and many versions), `real/` (sanitized real saves), `json_v3_6_0/` (JSON exported by upstream 3.6.0, which must keep importing). |
| `tests/tools/` | `gen_fixtures.py`, `sanitize_save.py`, `get_game_data.py`. |

Main tests: `test_roundtrip.py` (every fixture reads and writes back identically),
`test_features.py` (runs every menu feature with typed answers), `test_locales.py`,
`test_layers.py`, `test_cli.py` (prompts, menu, undo, updater), `test_commands.py`, `test_schema.py`.

## How to do common things

- **Add a menu feature**: write it in `cli/edits/`, add it to the tree in `cli/feature_handler.py`,
  and add its name and messages to `src/bcsfe/files/locales/` (`en`, `vi` and `tw`).
  `test_features.py` runs it automatically; make sure it doesn't crash on odd answers or without
  game data or network.
- **Show a message**: use a locale key, not a string (`color.color_print_key("key", name=...)`,
  `core.localize("key", ...)`, `core.messages.show(...)` from core). `tests/test_locales.py` fails if
  the English, Vietnamese or Traditional Chinese text is missing. Format: see
  [LOCALIZATION.md](LOCALIZATION.md) (`{name}` placeholders, `{{other_key}}` references,
  `<@s>...</>` colours, `$(...)` conditions).
- **Change the save format**: edit `save_layout.py` and the section's schema, then run the round-trip
  tests on every fixture. Version-dependent fields use `when=ge(<version>)`, where the version is
  the game version as an integer (`15.7.0` is `150700`).
- **Add a setting**: add a `ConfigKey` and its default in `core/io/config.py`, its editor in
  `cli/edits/settings.py`, and its text in all three languages.
- **Record the change**: add a line to `CHANGELOG.md` under `[Unreleased]` for anything a user would
  notice. Update `README.md` if it describes what you changed.

## Things that have bitten us

- **Bundled files are copied to the data folder** (`~/.local/share/bcsfe` on Linux) on first run,
  and the editor reads them from there. After changing anything under `src/bcsfe/files/`, run the
  editor once with `--force-migrate`, or you'll test the old copy.
- **Menu tests run with and without game data.** `tests/tools/get_game_data.py` downloads one
  version (en 15.6.1) into `tests/game_data/`; without it the `game_data` cases just don't run, so
  run it once. Tests use a throwaway copy, because menus change it (the game data manager deletes
  versions). Never point a test at the real folder.
- **Feature tests share one config.** A feature that changes a setting (e.g. the language) would
  leak into later tests; `tests/test_features.py` restores the config after each test. Anything
  that depends on directory order must sort (the locale list is sorted for this reason).
- **pip won't reinstall a version that's already installed**, even with `--upgrade`, and this fork's
  commits often share a version number. The updater runs
  `pip install --force-reinstall --no-deps git+...@<sha>`, then `pip install git+...@<sha>` for any
  new dependencies. Keep it that way.
- **Game data sources.** `core/server/game_data_getter.py` tries the configured source, then
  every URL in `SOURCES` (battlecatsmodding, gitlab, then `meowzerskittycat/bcdata`, a mirror on
  GitHub releases that its own workflow syncs daily). Never ask the user which source to use; just
  fall through. `RequestHandler.get` returns non-200 responses too, so check the status.
  `tests/test_game_data.py` fakes the network for this.
- **Unparsed trailing bytes.** Data after the last known field is kept as `remaining_data` and
  written back unchanged. 15.x saves have more there (version markers 140500 ... 150700 with mostly
  zero data between). Upstream doesn't parse it either. Don't guess at fields without real saves
  that use them.
- **Output piped into `head`** closes the pipe early; `bcsfe export SAVE -` handles
  `BrokenPipeError`. New commands that print should too.
- **Windows**: paths and file locks differ, and CI runs Windows on every push. Use `core.Path`
  rather than string paths.

## Conventions

- Keep changes small and in the style of the surrounding code. Comments explain why, not what.
- pyright runs in strict mode. Annotate new code fully; avoid `Any` where a type is knowable.
- ruff's security rules (`S602`, `S604`, `S605`) are on: don't build shell commands from strings;
  pass argument lists to `core.Command`.
- Commit messages: a short imperative subject line, then a body that says why.
- Work on a branch and open a pull request against `main`; don't push to `main` directly.
