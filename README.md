<div align="center">

<h1>Battle Cats Save File Editor</h1>

<p><b>A command line save editor for The Battle Cats, made safer and easier to use.</b></p>

<p>
<a href="https://github.com/meowzerskittycat/BCSFE/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/meowzerskittycat/BCSFE/actions/workflows/ci.yml/badge.svg"></a>
<img alt="Python 3.14+" src="https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white">
<img alt="Game version up to 15.7" src="https://img.shields.io/badge/game%20version-up%20to%2015.7-orange">
<img alt="Runs on Android, Windows, macOS and Linux" src="https://img.shields.io/badge/runs%20on-Android%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
<a href="LICENSE"><img alt="License: GPLv3" src="https://img.shields.io/badge/license-GPLv3-blue"></a>
</p>

<p>
<a href="#installation">Install</a> ·
<a href="#editing-your-save">Edit your save</a> ·
<a href="#using-the-menu">Menu tips</a> ·
<a href="#avoiding-bans">Avoid bans</a> ·
<a href="#command-line">Command line</a> ·
<a href="https://github.com/meowzerskittycat/BCSFE/issues">Report a bug</a>
</p>

</div>

A fork of [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python) by fieryhenry.

> [!IMPORTANT]
> `pip install bcsfe` installs **upstream's** editor, not this fork. Use the
> [install commands below](#installation) instead. Report bugs for this fork in
> [its issues](https://github.com/meowzerskittycat/BCSFE/issues); upstream's Discord and Codeberg
> don't support it.

## What this fork adds

| Feature | What it means for you |
|---|---|
| **Undo** | Step back through your last 10 edits from the main menu. |
| **Safer editing** | If a feature fails, or you press <kbd>Ctrl</kbd>+<kbd>C</kbd>, your save is left exactly as it was. |
| **Easier menus** | Stays in the same category after an edit, `0` goes back, and you can type a feature's name to run it. Blank or `q` cancels a question, and wrong input is asked again instead of crashing. |
| **Command line tools** | `bcsfe info`, `check`, `export` and `import`, for scripts and bug reports. |
| **Bug fixes** | No more save corruption after a JSON import, crowns and maps unlock properly, and [more](CHANGELOG.md). |
| **Tested** | Over 550 tests, run on Windows, macOS and Linux, using saves from all four regions (`en`, `jp`, `kr`, `tw`) and game versions 9.0 to 15.7. |

## Installation

The editor doesn't have to run on the device the game is on. Any device with Python 3.14 or newer
works. Open the section for your platform:

<details open>
<summary><b>Android (Termux)</b></summary>

1. Install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) or
   [GitHub](https://github.com/termux/termux-app/releases). The Google Play version doesn't fully
   work.
2. Open Termux and run:

   ```sh
   termux-setup-storage
   pkg update && pkg upgrade
   pkg install python git
   pip install git+https://github.com/meowzerskittycat/BCSFE
   ```

3. Start the editor:

   ```sh
   bcsfe
   ```

Warnings about **tkinter** are normal on Android: you type file paths instead of picking files in a
window. Your downloads folder is `/sdcard/Download/`, so a save there is
`/sdcard/Download/SAVE_DATA`.

</details>

<details>
<summary><b>Windows</b></summary>

1. Install [Python 3.14+](https://www.python.org/downloads/) (tick **Add python.exe to PATH**) and
   [Git](https://git-scm.com/downloads).
2. In PowerShell, run:

   ```powershell
   py -m pip install git+https://github.com/meowzerskittycat/BCSFE
   py -m bcsfe
   ```

</details>

<details>
<summary><b>macOS</b></summary>

1. Install [Python 3.14+](https://www.python.org/downloads/) and
   [Git](https://git-scm.com/downloads) (or run `xcode-select --install`).
2. In Terminal, run:

   ```sh
   python3 -m pip install git+https://github.com/meowzerskittycat/BCSFE
   python3 -m bcsfe
   ```

</details>

<details>
<summary><b>Linux</b></summary>

Install Python 3.14+ and git with your package manager, then:

```sh
pipx install git+https://github.com/meowzerskittycat/BCSFE
bcsfe
```

For the file picker window, also install `tk` (often called `python3-tk` or `python-tk`).

</details>

<details>
<summary><b>iOS (a-Shell)</b></summary>

Check `python3 --version` first. If a-Shell's Python is older than **3.14**, the editor won't
install.

```sh
pip install git+https://github.com/meowzerskittycat/BCSFE
python3 -m bcsfe
```

</details>

<details>
<summary><b>Updating and uninstalling</b></summary>

The easiest way to update is **Editor → Check for updates** in the editor. To do it yourself:

| | pip | pipx |
|---|---|---|
| **Update** | `pip install --force-reinstall --no-deps git+https://github.com/meowzerskittycat/BCSFE` | `pipx reinstall bcsfe` |
| **Uninstall** | `pip uninstall bcsfe` | `pipx uninstall bcsfe` |

On Windows, put `py -m` before `pip`. Plain `pip install -U` and `pipx upgrade` can't see new commits
that keep the same version number, so they often do nothing. If you're switching from upstream's
editor, the pip update command replaces it.

</details>

## Editing your save

| Step | Where | What to do |
|:---:|---|---|
| 1 | Game | **Settings → Change Account / Device → Change Device → Retrieve Data from Old Device**, then tap **Save Data to Server**. Note the transfer and confirmation codes. |
| 2 | Editor | Choose **Download save file using transfer and confirmation code**. Enter both codes and your region: `en`, `jp`, `kr` or `tw`. |
| 3 | Editor | Edit whatever you like (see [menu tips](#using-the-menu)). |
| 4 | Editor | In **Save Management**, choose **Upload save file to server and get transfer and confirmation code**. If it fails, try again. |
| 5 | Game | Tap **Close Game → Cancel Data Transfer** (and **Start Game From Beginning** if asked). |
| 6 | Game | **Change Account / Device → Resume Data Transfer → Transfer Data to New Device**, enter the new codes and tap **Resume Transfer**. |

`en` also covers the Italian, Spanish, French, Thai and German versions. Repeat these steps every
time you edit: the editor's copy and the game's copy of your save aren't linked.

Each time you load a save, the editor keeps a dated copy of it (the newest 50; change this in
**Config**). To go back to one, choose **Restore a backup** when loading.

> [!WARNING]
> **Keep your transfer codes private.** Anyone with them can take your account. Linking a Google or
> Apple account may limit how often you can transfer, so it's safest not to link one.

## Using the menu

| Type | To |
|---|---|
| A number, e.g. `3` | Open a category or run a feature |
| `0` | Go back |
| Text, e.g. `cat food` | Search for a feature. An exact name runs it straight away |
| <kbd>Enter</kbd> on the main menu | List every feature |
| <kbd>Enter</kbd> or `q` on a question | Keep the current value, or cancel |
| `1-5`, `1 3 7` or `all` | Pick several items at once, where a list allows it |
| <kbd>Ctrl</kbd>+<kbd>C</kbd> | Cancel the current feature without changing the save. On the main menu it exits, asking whether to save first |

Made a mistake? Pick **Undo last edit** from the main menu. The number next to it is how many edits
you can undo.

The language, colour theme and other settings are under **Editor → Config**. The editor comes
in English, Vietnamese and Traditional Chinese, with a `default` and a `discord` theme. To add a
language, see [LOCALIZATION.md](LOCALIZATION.md).

## Avoiding bans

Directly adding **cat food**, **rare tickets** or **platinum tickets** is the most likely way to get
banned. Try these instead:

| Instead of adding… | Use |
|---|---|
| Platinum tickets | **Platinum Shards** |
| Rare tickets | **Rare Ticket Trade** |
| Cat food | What you'd buy with it (XP, battle items, catamins, leadership), or clear and unclear catnip missions in **Catnip Challenges / Missions**, then collect the reward in the game |
| Any tickets | The cats and upgrades you want, directly |

If you're banned, use **Account → Unban Account / Fix Save Used Elsewhere Error**, or upload the
save again.

## Command line

Besides the menu, `bcsfe` has commands that don't ask anything, for scripts and bug reports:

```sh
bcsfe info SAVE_DATA                 # region, game version, cat food, tickets...
bcsfe check SAVE_DATA                # can the editor read and write this save safely?
bcsfe export SAVE_DATA save.json     # save -> JSON (use - to print it instead)
bcsfe import save.json SAVE_DATA     # JSON -> save
```

If a game update breaks the editor, include the output of `bcsfe check` in your bug report.

<details>
<summary><b>Options for the menu</b></summary>

| Option | Does |
|---|---|
| `-i`, `--input-path PATH` | Open this save straight away |
| `-c`, `--config-path PATH` | Use a different config file |
| `-d`, `--data-dir PATH` | Keep the editor's data somewhere else |
| `-g`, `--game-data-dir PATH` | Keep downloaded game data somewhere else |
| `-l`, `--log-path PATH` | Write the log somewhere else |
| `--transfer-backup-path PATH` | Where to back up the save after a transfer |
| `--force-migrate` | Copy the editor's bundled files into its data folder again |
| `-v`, `--version` | Print the version and exit |

Set the `NO_COLOR` environment variable (e.g. `NO_COLOR=1 bcsfe`) to turn colours off.

</details>

<details>
<summary><b>Rooted devices</b></summary>

| Method | Steps |
|---|---|
| **adb** (from a PC) | Put adb from [platform-tools](https://developer.android.com/studio/releases/platform-tools) on your PATH, or set its path in the editor config. Choose **Pull save file from device using adb**, edit, then in **Save Management** choose **Use adb to push the save file to a device**. |
| **On the device** | Run the editor in Termux (possibly with `sudo`). Choose **Pull save file from root storage**, edit, then push it back from **Save Management**. |

</details>

## This editor is free

> [!CAUTION]
> If you paid for this editor, or for a service built on it, **you were scammed**. It's free and
> open source under the GPL, and anyone can install it with the commands above.

## Development

```sh
git clone https://github.com/meowzerskittycat/BCSFE
cd BCSFE
pip install -e ".[dev]"
python tests/tools/get_game_data.py                    # game data for the menu tests
pytest                                                 # tests
ruff check src tests && ruff format --check src tests  # lint and formatting
pyright                                                # strict type checking
```

The tests read and write every save in `tests/fixtures/` and check that the output is byte for byte
identical, drive the menus with typed answers, and check that every message the code shows has
English text. `pytest --all-answers` also runs every answer set (slower; CI does this on pull
requests). CI runs lint and type checks, then the tests on Windows, macOS and Linux for pull
requests, and on Windows and Linux for pushes to `main`.

<details>
<summary><b>Where things live</b></summary>

| Task | How |
|---|---|
| Understand the layout | `bcsfe.core` reads, edits and writes saves and never imports the CLI (a test checks this). `bcsfe.cli` is the menu built on top. Core talks to the user only through `core.messages`. |
| Change the save format | The whole save is declared once, in order, in `core/io/save_layout.py`. |
| Add a save section | Declare it with `bcsfe.core.io.schema` (see `core/game/catbase/medals.py`). Stage sections share `core/game/map/stage_grid.py`. |
| Add a menu feature | Put the editor in `cli/edits/` and list it in `cli/feature_handler.py`. Ask questions with `cli/prompt.py`, and add its messages to `files/locales/en/` (`tests/test_locales.py` checks). |
| Test with real saves | Copy them into `tests/saves/` (gitignored). Real saves contain your account's inquiry code and tokens, so never commit them as they are. |
| Keep a real save as a fixture | `python tests/tools/sanitize_save.py path/to/save` replaces those details and writes the save to `tests/fixtures/real/`. |
| Synthetic saves | Made by `tests/tools/gen_fixtures.py`. Regenerate them only on purpose (e.g. for a new game version), never to make a failing test pass. |
| Translate the editor | See [LOCALIZATION.md](LOCALIZATION.md). |
| Work with an AI coding agent | [AGENTS.md](AGENTS.md) has the setup, checks and rules; `CLAUDE.md`, `GEMINI.md` and `.github/copilot-instructions.md` point to it. |

</details>

## Credits

- **[fieryhenry](https://codeberg.org/fieryhenry)** wrote
  [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python), which this fork is based on.
- **Lethal's editor**, [beeven/battlecats](https://github.com/beeven/battlecats) and
  [csehydrogen/BattleCatsHacker](https://github.com/csehydrogen/BattleCatsHacker) showed how to
  patch the save data.
- **HungJoesifer** contributed the Vietnamese translation and the `discord` theme.
- **LinYuAn** contributed the Traditional Chinese translation.

## License

[GNU GPLv3](LICENSE), as in upstream.
