# Translating the editor

The editor ships in English, Vietnamese (`vi`) and Traditional Chinese (`tw`). Any message that
isn't translated yet is shown in English, so a partial translation still works.

## Start a new language

1. Run the editor and open **Editor → Config → Language → Create New Locale**.
2. Enter a language code (like `de` or `pt-BR`), your name, and the language's name.
3. The editor copies the English files and prints the new folder's path, e.g.
   `~/.local/share/bcsfe/locales/de`. Open that folder.

## Translate

Each `.properties` file holds lines like `key=text`. Translate the text after `=` and leave the key
alone.

| In the English text | What to do |
|---|---|
| `{name}` | Keep it exactly as it is. The editor puts a value there, like a cat's name or a number. |
| `{{other_key}}` | Another message is inserted here. You can move or remove it. |
| `<@s>…</>`, `<@e>…</>`, `<@su>…</>`… | Colours. Keep them around the same words where you can. |
| `\n` | A line break. |
| `$(…)` | Text that changes with a value (e.g. plurals). Translate the words, keep the structure. |

Restart the editor to see your changes. To list what's still untranslated, turn on
**Editor → Config → Show missing locale keys** and restart. Keys missing from your files are
listed (extra keys are fine).

## Update an existing translation

New features add English messages that the other languages don't have yet. To find them, switch the
editor to that language and turn on **Show missing locale keys** as above. The translations live in
[`src/bcsfe/files/locales/`](src/bcsfe/files/locales/).

## Send it in

Copy your folder to `src/bcsfe/files/locales/<code>/` in a fork of
[this repository](https://github.com/meowzerskittycat/BCSFE), add yourself to `metadata.json`, and
open a pull request. If you'd rather not use git, attach a zip of the folder to an
[issue](https://github.com/meowzerskittycat/BCSFE/issues).

The tests check that every translation keeps the `{placeholders}` of its English text, that
every `{{reference}}` points to a real message, and that the bundled translations have every
English message:

```sh
pytest tests/test_locales.py
```

If you changed files under `src/bcsfe/files/` and the editor doesn't pick them up, run it once with
`--force-migrate` to copy them into its data folder.
