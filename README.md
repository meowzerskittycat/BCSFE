<div align="center">

# 🐱 Battle Cats Save File Editor

**A command line save editor for The Battle Cats, made safer and easier to use.**

[![CI](https://github.com/meowzerskittycat/BCSFE/actions/workflows/ci.yml/badge.svg)](https://github.com/meowzerskittycat/BCSFE/actions/workflows/ci.yml)
![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)
![Game version 15.7](https://img.shields.io/badge/game%20version-up%20to%2015.7-orange)
![Platforms](https://img.shields.io/badge/runs%20on-Android%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)

[Install](#-installation) · [Edit your save](#-editing-your-save) · [Menu tips](#-using-the-menu) · [Avoid bans](#%EF%B8%8F-avoiding-bans) · [Report a bug](https://github.com/meowzerskittycat/BCSFE/issues)

</div>

---

A fork of [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python) by fieryhenry.

> [!IMPORTANT]
> `pip install bcsfe` installs **upstream's** editor, not this fork. Use the [install commands below](#-installation).
>
> Report bugs in [this repo's issues](https://github.com/meowzerskittycat/BCSFE/issues). Upstream's Discord and Codeberg don't support this fork.

## ✨ What this fork adds

| | Feature | What it means for you |
|---|---|---|
| ↩️ | **Undo** | Step back through your last 10 edits from the main menu. |
| 🛡️ | **Safer editing** | If a feature fails, or you press Ctrl+C, your save is left exactly as it was. |
| 🧭 | **Easier menu** | Stays in the same category after an edit; `0` goes back; type a name to run a feature. |
| ⌨️ | **Command line tools** | `bcsfe info`, `check`, `export` and `import`, for scripts and bug reports. |
| 🐛 | **Bug fixes** | No more save corruption after a JSON import, crowns and maps unlock properly, and [more](CHANGELOG.md). |
| ✅ | **Tested** | Real saves from several regions and versions, checked on Windows, macOS and Linux. |

## 📦 Installation

The editor can run on any device. It doesn't have to be the one the game is on. Click your platform:

<details open>
<summary><b>🤖 Android (Termux)</b></summary>

<br>

1. Install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) or [GitHub](https://github.com/termux/termux-app/releases).

   > [!WARNING]
   > The Google Play version of Termux doesn't fully work.

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

> [!NOTE]
> Warnings about **tkinter** are normal on Android. You'll type file paths instead of picking them
> in a window. Your downloads folder is `/sdcard/Download/`, e.g. `/sdcard/Download/SAVE_DATA`.

</details>

<details>
<summary><b>🪟 Windows / 🍎 macOS</b></summary>

<br>

1. Install [Python 3.14+](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads).
2. In a terminal (PowerShell on Windows), run:

   ```sh
   py -m pip install git+https://github.com/meowzerskittycat/BCSFE
   py -m bcsfe
   ```

> [!TIP]
> On macOS, or if `py` isn't found, use `python3` instead of `py`.

</details>

<details>
<summary><b>🐧 Linux</b></summary>

<br>

Install Python 3.14+ and git with your package manager, then:

```sh
pipx install git+https://github.com/meowzerskittycat/BCSFE
bcsfe
```

> [!TIP]
> For the file picker window, install `tk` (it may be called `python-tk` or `python3-tk`).

</details>

<details>
<summary><b>📱 iOS (a-Shell)</b></summary>

<br>

> [!CAUTION]
> Run `python3 --version` first. If a-Shell's Python is older than **3.14**, the editor won't install.

```sh
pip install git+https://github.com/meowzerskittycat/BCSFE
python3 -m bcsfe
```

</details>

<details>
<summary><b>🔄 Updating / uninstalling</b></summary>

<br>

| Action | pip | pipx |
|---|---|---|
| Update | `pip install -U git+https://github.com/meowzerskittycat/BCSFE` | `pipx upgrade bcsfe` |
| Uninstall | `pip uninstall bcsfe` | `pipx uninstall bcsfe` |

If you're switching from upstream's editor, the update command replaces it.

</details>

## 🎮 Editing your save

| Step | Where | What to do |
|:---:|---|---|
| 1 | 🎮 Game | **Settings → Change Account / Device → Change Device → Retrieve Data from Old Device**, then tap **Save Data to Server**. Note the transfer and confirmation codes. |
| 2 | 💻 Editor | Choose **Download save file using transfer and confirmation code**. Enter both codes and your region: `en`, `jp`, `kr` or `tw`. |
| 3 | 💻 Editor | Edit whatever you like (see [menu tips](#-using-the-menu)). |
| 4 | 💻 Editor | In **Save Management**, choose **Upload save file to server and get transfer and confirmation code**. If it fails, try again. |
| 5 | 🎮 Game | Tap **Close Game → Cancel Data Transfer** (and **Start Game From Beginning** if asked). |
| 6 | 🎮 Game | **Change Account / Device → Resume Data Transfer → Transfer Data to New Device**, enter the new codes and tap **Resume Transfer**. 🎉 |

> [!NOTE]
> `en` also covers the Italian, Spanish, French, Thai and German versions. Repeat these steps every
> time you edit, because the editor's copy and the game's copy aren't linked.

> [!WARNING]
> **Keep your transfer codes private.** Anyone with them can take your account. Linking a Google or
> Apple account may limit how often you can transfer, so it's safest not to link one.

## 🧭 Using the menu

| Type | To |
|---|---|
| `3` (a number) | Open a category or run a feature |
| `0` | Go back |
| `cat food` (text) | Search; an exact name runs straight away |
| Enter on the main menu | List every feature |
| Enter on a question | Keep the current value, or cancel (`q` works too) |
| <kbd>Ctrl</kbd>+<kbd>C</kbd> | Cancel the current feature, leaving the save untouched. At the main menu it exits, asking whether to save first |

Made a mistake? Pick **Undo last edit** from the main menu. The number next to it is how many edits
you can undo.

## ⚠️ Avoiding bans

Directly adding **cat food**, **rare tickets** or **platinum tickets** is the most likely way to get
banned. Try these instead:

| Instead of adding… | Use |
|---|---|
| 💎 Platinum tickets | **Platinum Shards** |
| 🎟️ Rare tickets | **Rare Ticket Trade** |
| 🥫 Cat food | What you'd buy with it (XP, battle items, catamins, leadership), or clear and unclear catnip missions in **Catnip Challenges / Missions**, then collect the reward in the game |
| 🎫 Any tickets | The cats and upgrades you want, directly |

> [!TIP]
> If you're banned, use **Account → Unban account**, or upload the save again.

## 🧰 More ways to use it

<details>
<summary><b>⌨️ Command line</b></summary>

<br>

```sh
bcsfe info SAVE_DATA                 # region, game version, cat food, tickets...
bcsfe check SAVE_DATA                # can the editor read and write this save safely?
bcsfe export SAVE_DATA save.json     # save -> JSON (use - to print it)
bcsfe import save.json SAVE_DATA     # JSON -> save
```

If a game update breaks the editor, include the output of `bcsfe check` in your bug report.
Set `NO_COLOR=1` to turn colours off.

</details>

<details>
<summary><b>🔓 Rooted devices</b></summary>

<br>

| Method | Steps |
|---|---|
| **adb** (from a PC) | Put adb from [platform-tools](https://developer.android.com/studio/releases/platform-tools) on your PATH, or set its path in the editor config. Choose **Pull save file from device using adb**, edit, then push it back from **Save Management**. |
| **On the device** | Run the editor in Termux (possibly with `sudo`). Choose **Pull save file from root storage**, edit, then push it back from **Save Management**. |

</details>

## 💸 This editor is free

> [!CAUTION]
> If you paid for this editor, or for a service built on it, **you were scammed**. It's free and
> open source under the GPL, and anyone can install it with the commands above.

## 🛠️ Development

<details>
<summary><b>Set up and run the checks</b></summary>

<br>

```sh
git clone https://github.com/meowzerskittycat/BCSFE
cd BCSFE
pip install -e ".[dev]"
pytest                                                 # tests
ruff check src tests && ruff format --check src tests  # lint and formatting
pyright                                                # strict type checking
```

The tests read and write every save in `tests/fixtures/` and check that the output is byte for
byte identical. They also drive the menus with typed answers. CI runs them on Windows, macOS and
Linux.

</details>

<details>
<summary><b>Where things live</b></summary>

<br>

| Task | How |
|---|---|
| Test with real saves | Copy them into `tests/saves/` (gitignored). Real saves contain your account's inquiry code and tokens, so never commit them as they are. |
| Keep a real save as a fixture | `python tests/tools/sanitize_save.py path/to/save` replaces those details and writes the save to `tests/fixtures/real/`. Its game progress stays in the file. |
| Synthetic saves | Made by `tests/tools/gen_fixtures.py`. Only regenerate them on purpose (e.g. for a new game version), never to make a failing test pass. |
| Add a save section | Declare it once with `bcsfe.core.io.schema` (see `core/game/catbase/medals.py`). Stage sections share `core/game/map/stage_grid.py`. |
| Translate the editor | See [LOCALIZATION.md](LOCALIZATION.md). |

</details>

## 🙏 Credits

- **[fieryhenry](https://codeberg.org/fieryhenry)** wrote [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python), which this fork is based on.
- **Lethal's editor**, [beeven/battlecats](https://github.com/beeven/battlecats) and [csehydrogen/BattleCatsHacker](https://github.com/csehydrogen/BattleCatsHacker) showed how to patch the save data.
- **HungJoesifer** contributed the Vietnamese translation and the `discord` theme.
- **LinYuAn** contributed the Traditional Chinese translation.

## 📄 License

[GNU GPLv3](LICENSE), as in upstream.
