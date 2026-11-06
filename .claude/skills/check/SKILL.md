---
name: check
description: Run every check CI runs on this repository (ruff lint, ruff format, strict pyright, pytest with all answer sets) and report the results. Use before committing or when asked whether the code is ready.
---

# Run the checks

Run these from the repository root with Python 3.14 or later (`python --version`; if the default
is older, find a 3.14 interpreter or virtualenv first). Run them all even if one fails, then report
each as passed or failed with the relevant output.

```sh
ruff check src tests
ruff format --check src tests
pyright
pytest --all-answers
```

- If `ruff format --check` fails, `ruff format src tests` fixes it; show the user what changed.
- If a round-trip test in `tests/test_roundtrip.py` fails, the save format changed. Find the cause
  in the code. Never regenerate the fixtures to make it pass.
- If `tests/test_locales.py` fails, a message key the code uses has no English text, or a
  translation's `{placeholders}` don't match the English. Add the English text in
  `src/bcsfe/files/locales/en/`.
- Never skip, xfail or loosen a test to get green.
