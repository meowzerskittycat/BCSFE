# Battle Cats Save File Editor (fork)

A command line save editor for The Battle Cats, supporting saves up to game version
15.7.

This is a fork of [BCSFE-Python](https://codeberg.org/fieryhenry/BCSFE-Python) by
fieryhenry. It needs Python 3.14 and adds:

- **Undo** for your last 10 edits, from the main menu.
- **Safer editing:** if a feature fails or you press Ctrl+C during it, your save is left as it
  was and you're back at the menu. The crash backup can no longer be half-written.
- **An easier menu:** after an edit it stays in the same category, `0` goes back, and typing a
  feature's name runs it.
- **Command line tools:** `bcsfe info`, `check`, `export` and `import`.
- **Bug fixes**, including save corruption after a JSON import, and stages that didn't unlock the
  next crown or map. See the [changelog](CHANGELOG.md).
- **Tests on real saves** from several regions and versions, run on Windows, macOS and Linux.

Report bugs and ask for features in [this repo's issues](https://github.com/meowzerskittycat/BCSFE/issues),
not upstream's Discord or Codeberg. They don't support this fork.

> [!IMPORTANT]
> `pip install bcsfe` installs **upstream's** editor from PyPI, not this fork. Use the commands
> below.

## Installation

You can run the editor on any device. It doesn't have to be the one the game is on.

### Android (Termux)

1. Install Termux from [F-Droid](https://f-droid.org/packages/com.termux/) or
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

Warnings about tkinter are normal on Android. You type file paths instead of picking them in a
window. Your downloads folder is `/sdcard/Download/`, for example `/sdcard/Download/SAVE_DATA`.

### Windows / macOS

1. Install [Python 3.14 or later](https://www.python.org/downloads/) and
   [Git](https://git-scm.com/downloads).

2. In a terminal (PowerShell on Windows), run:

   ```sh
   py -m pip install git+https://github.com/meowzerskittycat/BCSFE
   py -m bcsfe
   ```

   Use `python3` instead of `py` on macOS, or if `py` isn't found.

### Linux

Install Python 3.14+ and git with your package manager, then:

```sh
pipx install git+https://github.com/meowzerskittycat/BCSFE
bcsfe
```

To get the file picker window, install `tk` (it may be called `python-tk` or `python3-tk`).

### iOS (a-Shell)

Run `python3 --version` in a-Shell first. If a-Shell's Python is older than 3.14, the editor won't
install there. Otherwise:

```sh
pip install git+https://github.com/meowzerskittycat/BCSFE
python3 -m bcsfe
```

### Updating and uninstalling

```sh
pip install -U git+https://github.com/meowzerskittycat/BCSFE   # update
pip uninstall bcsfe                                            # uninstall
```

With pipx, use `pipx upgrade bcsfe` and `pipx uninstall bcsfe`. If you're switching from upstream's
editor, the update command replaces it.

## Editing your save

1. In the game, go to **Settings → Change Account / Device → Change Device → Retrieve Data from Old
   Device**, then tap **Save Data to Server**. You get a transfer code and a confirmation code.

2. In the editor, choose **Download save file using transfer and confirmation code** and enter
   both codes and your region (`en`, `jp`, `kr` or `tw`; `en` also covers the it, es, fr, th and de
   versions).

3. Edit what you want (see [using the menu](#using-the-menu)).

4. In **Save Management**, choose **Upload save file to server and get transfer and confirmation
   code**. If it fails, try again.

5. In the game, tap **Close Game**, then **Cancel Data Transfer** (and **Start Game From Beginning**
   if it asks).

6. Go to **Change Account / Device → Resume Data Transfer → Transfer Data to New Device**, enter
   the new codes and tap **Resume Transfer**.

Repeat this every time you edit: the editor's copy and the game's copy aren't linked.

Keep your transfer codes private. Anyone with them can take your account. Linking a Google or
Apple account may limit how often you can transfer, so it's safest not to link one.

### Using the menu

- Type a **number** to open a category or run a feature, and `0` to go back.
- Type **text** to search, e.g. `cat food` or `legend`. An exact name runs straight away.
- Press **Enter** on the main menu to list every feature.
- Press **Enter** on a question to keep the current value or cancel. You can also type `q`.
- **Ctrl+C** cancels the current feature and leaves the save untouched. At the main menu it exits,
  asking whether to save first.
- **Undo last edit** steps back through your last 10 edits.

### Avoiding bans

Directly adding cat food, rare tickets or platinum tickets is the most likely way to get banned.
Safer options:

- **Platinum tickets:** use **Platinum Shards**.
- **Rare tickets:** use **Rare Ticket Trade**.
- **Cat food:** edit in what you'd buy with it instead (XP, battle items, catamins, leadership), or
  clear and unclear catnip missions in **Catnip Challenges / Missions** and collect the reward in the
  game.
- **Tickets:** edit in the cats and upgrades you want directly.

If you are banned, use **Account → Unban account**, or upload the save again.

### Rooted devices

- **With adb:** put adb from [platform-tools](https://developer.android.com/studio/releases/platform-tools)
  on your PATH, or set its path in the editor config. Choose **Pull save file from device using
  adb**, edit, then push it back from **Save Management**.
- **On the device:** run the editor in Termux (possibly with `sudo`), choose **Pull save file from
  root storage**, edit, then push it back from **Save Management**.

### Command line

Some things work without the menus, which is handy for scripts:

```sh
bcsfe info SAVE_DATA                 # region, game version, cat food, tickets...
bcsfe check SAVE_DATA                # can the editor read and write this save safely?
bcsfe export SAVE_DATA save.json     # save -> JSON (use - to print it)
bcsfe import save.json SAVE_DATA     # JSON -> save
```

If a game update breaks the editor, include the output of `bcsfe check` in your bug report.

Set `NO_COLOR=1` to turn colours off.

## This editor is free

If you paid for this editor or for a service built on it, you were scammed. It's free and open
source under the GPL, and anyone can install it with the commands above.

## Development

```sh
git clone https://github.com/meowzerskittycat/BCSFE
cd BCSFE
pip install -e ".[dev]"
pytest                                            # tests
ruff check src tests && ruff format --check src tests
pyright                                           # strict type checking
```

The tests read and write every save in `tests/fixtures/` and check that the output is byte for byte
identical. They also drive the menus with typed answers. CI runs them on Windows, macOS and Linux.

- **Real saves:** copy them into `tests/saves/`. That folder is gitignored because real saves
  contain your account's inquiry code and tokens. To keep one as a fixture, run
  `python tests/tools/sanitize_save.py path/to/save`. This replaces those details and writes the
  save to `tests/fixtures/real/`. Its game progress stays in the file.
- **Synthetic saves:** these are made by `tests/tools/gen_fixtures.py`. Only regenerate them on
  purpose (for example for a new game version), never to make a failing test pass.
- **New save sections:** declare them once with `bcsfe.core.io.schema` (see
  `core/game/catbase/medals.py`). Stage-progress sections share the model in
  `core/game/map/stage_grid.py`.
- **Translations:** see [LOCALIZATION.md](LOCALIZATION.md).

## Credits

- [fieryhenry](https://codeberg.org/fieryhenry) wrote BCSFE-Python, which this fork is based on.
- Lethal's editor, plus [beeven/battlecats](https://github.com/beeven/battlecats) and
  [csehydrogen/BattleCatsHacker](https://github.com/csehydrogen/BattleCatsHacker), showed how to
  patch the save data.
- HungJoesifer contributed the Vietnamese translation and the `discord` theme, and LinYuAn
  contributed the Traditional Chinese translation.

## License

GNU GPLv3, as in upstream: see [LICENSE](LICENSE) or
<https://www.gnu.org/licenses/gpl-3.0.en.html>.
