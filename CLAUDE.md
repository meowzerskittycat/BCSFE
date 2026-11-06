# Claude Code

Everything an agent needs for this repository is in AGENTS.md, imported here so it's always loaded:

@AGENTS.md

## Claude Code specifics

- `/check` runs every check CI runs (`.claude/skills/check/SKILL.md`). Run it before every commit.
- When you learn something about this project that would have saved you time (a trap, a rule from
  the user, a reason behind the code), add it to AGENTS.md (under "Things that have bitten us" or
  "Hard rules") so the next session, and other agents, know it too. Don't put it here unless it
  only applies to Claude Code.
- The user may test with their own saves in `tests/saves/`. Read them only to run tests; never copy
  their contents (inquiry code, tokens, transfer codes) into output, commits or files.
