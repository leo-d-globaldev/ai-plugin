---
name: ship-doctor
description: Use when the GDV AI-KIT seems not to work on Codex - a skill did not load, a push was not blocked or was blocked unexpectedly, hooks do nothing, the tracker does not answer, after installing or updating the plugin, or before a new person starts. Read-only health check with one fix per problem. Never edits a file or installs anything.
---

# ship-doctor (Codex)

Read-only. Each check is **ok**, **problem** (with the one fix) or **not checked** (with why). Read `../../CONVENTIONS.md` first. Paths `../../X` are relative to this folder; commands run in the repo.

## Checks

| # | Check | Problem when |
|---|---|---|
| 1 | Package version (`../../VERSION`; the installed plugin's `.claude-plugin/plugin.json` carries the same number) | `../../VERSION` missing |
| 2 | `## AI-KIT` section in `CLAUDE.md` | missing; a value outside the allowed ones (CONVENTIONS §1) |
| 3 | Codex reads it: `project_doc_fallback_filenames` includes `CLAUDE.md` in `~/.codex/config.toml` (or the project `.codex/config.toml`), or `AGENTS.md` points to the section | neither: Codex does not see the config. Fix: `$gdv-ai-kit:ship-init` |
| 4 | Data class | missing (treated as B); C while Codex works on this code: stop using Codex here |
| 5 | Role in `AGENTS.local.md` (`## AI-KIT me`) | missing or a value outside po, ba, dev, lead, qc, pm, all; the file not in `.gitignore` |
| 6 | Intent home | the folder or docs repo does not exist |
| 7 | Tracker | `adapter` set but its MCP tools are missing from this session; a `get-item` on a key the person gives fails |
| 8 | Hooks trusted | `python3` missing; the gate does not answer a dry run: `echo '{"tool_name":"Bash","tool_input":{"command":"git push --force"},"cwd":"'$PWD'"}' \| python3 ../../hooks/gates_codex.py` must print a JSON with `deny` (resolve the path from this folder); and ask the person whether `/hooks` shows the plugin's hooks as trusted (not checkable from here: say so) |
| 9 | Prefix rules | `~/.codex/rules/gdv.rules` missing (information) |
| 10 | Git hook | `.git/hooks/pre-push` missing or not executable (information) |
| 11 | Git ignore | `.gdv/` not ignored; `.ai/` ignored (the work log must be committed) |
| 12 | Skill list | the Codex skill list (`/skills`) omits a gdv-ai-kit skill (the 2% description budget): fix is `skills.max_context_tokens` in `config.toml` |
| 13 | Leftovers | work logs still open (`python3 ../../scripts/worklog_codex.py pending`); `.gdv/bugfix-lock.json` whose bug intent is `merged` or later |
| 14 | Model and effort | `python3 ../../scripts/kit-config.py models` prints a `problem:` line (a `model-*` value in `CLAUDE.md`, `AGENTS.local.md` or `CLAUDE.local.md` with a bad shape or an effort Codex does not know). Whether `codex exec` accepts the model on this account is not checked |

## Answer

1. First line: the project folder and the package version.
2. The table: `#`, check, result, detail or fix in one line.
3. One line per key set, from the script: `Models: easy gpt-x/medium (CLAUDE.md) · verify ...`; none set → `Models: not set (Codex uses its own default)`.
4. A last line: the first thing to fix, or "all ok".
