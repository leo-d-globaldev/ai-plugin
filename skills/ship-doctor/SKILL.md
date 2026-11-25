---
name: ship-doctor
description: Use when the GDV AI-KIT seems not to work as expected - a skill did not load, a push was blocked unexpectedly, the tracker does not answer, after installing or updating the plugin, or before a new person starts. Read-only health check of the plugin version, the AI-KIT section, the role, the intent home and docs repo, the tracker connection, the hooks, the gitignore and leftovers of the old 0.x workflow, with one fix per problem. Never edits a file or installs anything.
---

# ship-doctor

Read-only. Each check is **ok**, **problem** (with the one fix) or **not checked** (with why). Fixes are mostly `/ship-init`. Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

## Checks

| # | Check | Problem when |
|---|---|---|
| 1 | Plugin version (`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`) | below 1.0.0 |
| 2 | `## AI-KIT` section in `CLAUDE.md` | missing; a value outside the allowed ones (CONVENTIONS §1); `## AI-DLC defaults` still present (old 0.x section) |
| 3 | Data class | missing (skills treat it as B); C while this session works on the code |
| 4 | Role, `mode` and `qc-url` in `CLAUDE.local.md` (`## AI-KIT me`) | role missing or a value outside po, ba, dev, lead, qc, pm, all; a `mode` outside manual, semi-auto (ignored by the kit); `CLAUDE.local.md` not in `.gitignore` |
| 5 | Intent home | the folder or docs repo does not exist; a docs repo not listed in `additionalDirectories` of `.claude/settings.local.json` or `.claude/settings.json` |
| 6 | Tracker | `adapter` set but the adapter's tools are missing (not signed in); a `get-item` on a key the person gives fails (only when they give one) |
| 7 | Hooks | `python3` missing (on Windows: `py` or `python` only, so the hooks cannot start); the gate does not answer a dry run: `echo '{"tool_name":"Bash","tool_input":{"command":"git push --force"},"cwd":"'$PWD'"}' \| python3 "${CLAUDE_PLUGIN_ROOT}/hooks/gates.py"` prints no `ask`; `.claude/gdv-gates.json` or the file in `GDV_GATES_EXTRA` is not valid JSON. Whether Claude Code loaded `hooks/hooks.json` cannot be read from inside a session: say not checked when the dry run passes |
| 8 | Git ignore | `.gdv/` not ignored; `.ai/` ignored (the work log must be committed) |
| 9 | Review gate state | the branch has commits after the last review in `.gdv/reviews/` (informational: code committed after the last review needs `/ship-review`; intent and `.ai/` commits do not) |
| 10 | Split intents | a `parent:` or `depends-on:` naming an intent that does not exist; a cycle in `depends-on`; a child without `owner:`; a parent `merged` while a child is not |
| 11 | Telemetry (must be off) | read the session's environment (`env \| grep -E '^(CLAUDE_CODE_ENABLE_TELEMETRY\|OTEL_)'`; print the names only, never a header value, which may hold a key): `CLAUDE_CODE_ENABLE_TELEMETRY` is `1`, or an `OTEL_*` exporter or endpoint variable is set (problem: usage data would leave the machine; the fix is the managed settings `CLAUDE_CODE_ENABLE_TELEMETRY` = `0`, see `${CLAUDE_PLUGIN_ROOT}/docs/platform.md`, Monitoring); `OTEL_RESOURCE_ATTRIBUTES` in the project's `.claude/settings.json` (left from 1.2.2 to 1.4.2: remove the key) |
| 12 | Leftovers | work logs still open (`work-log.py pending`); `.gdv/bugfix-lock.json` whose bug intent is `merged` or later; `plans/KEY.md` at the repo root (0.x); old commands in `CLAUDE.md`, `README` or `docs/`: `grep -rEn '/ship-(dev|ba|lead|pm|qc)-|/ship-next'` (replace them with the 1.x skills, see the plugin README) |
| 13 | Model and effort | `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kit-config.py" models` prints a `problem:` line (a value of `model-easy`, `model-medium`, `model-hard`, `model-verify` or `model-review`, in `CLAUDE.md` or `CLAUDE.local.md`, with a bad shape or an effort outside `low|medium|high|xhigh|max`). Whether the host applies them is not checked (only a session start shows it; the work log records what ran) |

## Answer

1. First line: the project folder and the plugin version.
2. The table: `#`, check, result, detail or fix in one line.
   Under it, one line: `Effective mode: X (from CLAUDE.local.md | CLAUDE.md | default)` (the doctor cannot see `--mode`; a local value outside manual, semi-auto shows the fallback source); when the local mode differs from the one in `CLAUDE.md`, add that as information, not a problem. Then one line per key set, from the script: `Models: easy sonnet/medium (CLAUDE.md) · verify opus/high (CLAUDE.local.md) · ...`; none set → `Models: not set (every session inherits)`.
3. **Fix first:** at most five problems, in table order, each with one command or step.
4. **Not checked:** what could not be read and why.

Never print a secret, a token or a `.env` value; check a variable is set with `[ -n "$NAME" ]`.
