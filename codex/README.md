# Codex target (0.3.0, for Codex CLI 0.169)

> In this repo this folder is the built plugin (`out/` in the source repo): read `out/X` below as `X` here. `build.py`, `src/` and `evals/` are not published.

The GDV AI-KIT for OpenAI Codex: the ten skills, the gates and the work log. `out/` is a complete Codex plugin named `gdv-ai-kit` (skills are called `$gdv-ai-kit:ship`, `$gdv-ai-kit:ship-build`): install it **instead of** the Claude plugin on a Codex machine, not next to it. It changes nothing in the Claude plugin and can be deleted alone (`rm -r targets/codex`).

## Why it exists

Codex runs the plugin's hooks, but the Claude gate logic does not hold there: Codex ignores the answer `ask` (the call goes through), and file edits arrive as the tool `apply_patch`, which the Claude hook matcher does not match. This layer fixes both:

- every `ask` becomes `deny` (fails closed), a core `deny` stays final;
- the files named in an `apply_patch` (add, update, delete, move) are checked as edits: protected paths and the bug-fix test lock;
- a person's approval is a token, see below.

The gate logic is not copied by hand: `build.py` makes a read-only copy of `hooks/gates.py` (`out/hooks/gates_core.py`) and `gates_codex.py` wraps it, so the two never drift. `python3 targets/codex/evals/run.py` runs every case of the Claude `evals/hook-cases.json` through the wrapper to prove it.

## What is gated

| Gate | When | On Codex |
|---|---|---|
| `review` | push of a commit without a review of HEAD | with `review-gate: block` (the default): deny, final, run `$gdv-ai-kit:ship-review` first; with `review-gate: ask`: deny, token |
| `force-push` | `git push --force`, `-f`, `+ref` | deny, token |
| `main-branch` | push to the main branch, or working on it | deny, token |
| `delete-branch` | deleting a remote branch | deny, token |
| `protected` | edit of migrations, infrastructure, CI (shell or `apply_patch`) | deny, token |
| `bugfix-lock` | edit of a locked test file during a bug fix | deny, token |
| `tracker-done`, `tracker-delete` | closing or deleting a ticket through an MCP tool | deny, token |

Also in `out/rules/gdv.rules`: prefix rules that make Codex ask before `terraform apply`, `kubectl apply`, `helm upgrade` and `git push`. These work without the hook trust step.

## Install (per person, once)

1. Clone this repo, then `codex plugin marketplace add ./ai-plugin/codex` and `codex plugin add gdv-ai-kit@gdv-ai-kit-codex`. A Claude plugin of the same name on the same machine would clash: use one of them per machine.
2. **Trust the hooks.** Codex runs a plugin hook only after the person trusts it: open Codex, type `/hooks`, trust the PreToolUse hook. A changed hook needs trust again. Without it the gates do nothing and Codex does not say so.
3. Copy `rules/gdv.rules` to `~/.codex/rules/` and merge `config.toml.template` into `~/.codex/config.toml` (it makes Codex read the project's `CLAUDE.md`, so the `## AI-KIT` section applies).
4. Optional second layer for pushes: `cp pre-push.sh .git/hooks/pre-push`, with `GDV_CODEX_HOOK` pointing at `gates_codex.py` when it is not next to the script.
5. In a project repo run `$gdv-ai-kit:ship-init` (Codex version: writes the `## AI-KIT` section, `AGENTS.local.md` with your role, `AGENTS.md`), then `$gdv-ai-kit:ship-doctor`.
6. Check: ask Codex to run `git push --force origin x`; it must say the force-push gate blocked it.

## Approval token

A denied call says which gate fired. The person says yes in chat, then the call is repeated with `GDV_APPROVED=GATE` in front (a shell command), or, for an edit, a first shell command `GDV_APPROVED=GATE true` approves that gate for 15 minutes. Every use is appended to `.gdv/approvals.log` (time, gate, hash of the command).

Honest limit: Codex has no way to ask the person from a hook, so the model types the token after the person agrees. It is a speed bump and a log, not a lock. Known weaknesses: the token text in any shell command (even an `echo` or a commit message, even one denied by another gate) records the approval; an approval is not used up, so within 15 minutes every edit (or MCP call) of that gate passes; a push approved in the pre-push hook also approves edits of that gate; the `git push` prefix rule does not match `git -C DIR push` or `git -c k=v push`. The locks are the `forbidden` and `prompt` rules and the git pre-push hook, which a person controls.

## Skills

`out/skills/` holds the ten Claude skills plus `policy-client-data`, **generated** from `skills/` (one source). The build changes only what must change on Codex:

| Claude text | Codex copy |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/X` | `../../X`, relative to the folder of the `SKILL.md` (a note at the top says so) |
| `/ship-build` and the like | `$gdv-ai-kit:ship-build` |
| `work-log.py`, `hooks/gates.py` | `worklog_codex.py`, `gates_codex.py` |
| `CLAUDE.local.md` (role) | `AGENTS.local.md` (a `CLAUDE.local.md` is still read as a fallback by the work log) |
| plan mode | "plan mode if this tool has one; otherwise draft in chat and write nothing until the owner says yes" |
| fresh session, `start_session` | an independent run: `codex exec - < .gdv/tmp/PROMPT.md` in the same folder; none possible, run inline and say so |
| `disable-model-invocation` | `agents/openai.yaml` with `allow_implicit_invocation: false` for `ship-init` and `ship-maintain` |

`ship-init` and `ship-doctor` are written for Codex (`src/skills/`): they set up and check `AGENTS.local.md`, the Codex config, the prefix rules and the `/hooks` trust, not Claude settings. The wording changes live in `src/wording.json`; when a source skill changes so that a phrase is no longer found, the build fails and names the phrase.

**Description budget.** Codex puts the skill list in about 2% of the context window (8,000 characters when the window is unknown) and shortens or drops descriptions beyond it. The build estimates the list (name + description + 24 characters per skill, now about 5,200) and fails above 8,000, and on angle brackets in a description. Fix when it fails: trim descriptions in the copy (trigger words first) or raise `skills.max_context_tokens` in `config.toml`.

## Work log

`out/scripts/worklog_codex.py` writes the same record as the Claude work log into `.ai/worklog/YYYY-MM/`, so `metrics.py` reads both. Differences: tokens and the model come from the Codex session file (`transcript_path`: last cumulative `total_token_usage` minus the value at start); `tokens` is `null` (and `tokens_total` too) when that file is unreadable; the plugin field reads `codex-VERSION`; `active_s` equals `elapsed_s`. `efforts` is the `effort` of the session file's `turn_context` items (a field of `TurnContextItem` in the Codex source; no real session file was available to confirm it, so the eval uses a synthetic line); empty when absent. `by_model` stays empty. `SessionEnd` closes logs left open (Codex allows 1 to 3 seconds; it runs no subprocess). A start whose session could not be identified (hooks not trusted) is left open instead of being closed by a guess. `worklog: strict` runs as `remind`: Codex edits arrive as `apply_patch`, which the work log does not intercept.

## Model and effort

Keys `model-easy`, `model-medium`, `model-hard`, `model-verify`, `model-review` (value `MODEL/EFFORT`) in the `## AI-KIT` section of `CLAUDE.md`, personal override in `AGENTS.local.md`; `scripts/kit-config.py models` reads them (it knows it is the Codex package because `worklog_codex.py` sits next to it). `$gdv-ai-kit:ship-build` and `$gdv-ai-kit:ship-review` add `-m MODEL` and `-c 'model_reasoning_effort="EFFORT"'` to the `codex exec` run of the verifier and the review; the building session is the person's own (`/model`). Read from the open-source Codex code (`openai/codex`, main), not run (no `codex` binary on the build machine): `-m/--model` and `-c key=value` (the value is parsed as TOML) exist for `codex exec`, the config key is `model_reasoning_effort`, and its values are `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, `ultra`, `persistent`; which of them a model accepts is the model's. **Unverified:** a real `codex exec -m ... -c ...` call and the model ids of a given account (the script only checks the shape; `ship-init` asks the person for ids and invents none).

## Tools per data class

Decided for C1 (2026-11-18): class A and B are allowed on any OpenAI account, a personal one included, **only with model training turned off**; class B with synthetic data only. Class C: none, and every skill stops on its first line. The customer contract stays the authority. The generated `policy-client-data` carries the same table.

## Files

| Path | What |
|---|---|
| `VERSION` | target version (changelog below) |
| `build.py` | builds `out/` (and `--dist DIR`) |
| `src/` | sources: `gates_codex.py`, `worklog_codex.py`, `hooks.json`, `rules.template`, `config.toml.template`, `pre-push.sh`, `AGENTS.md.template`, `transform.py`, `wording.json`, `skills/` (Codex-own init and doctor), `agents/`, `plugin.json.tmpl` |
| `out/` | generated, committed: what a person installs |
| `evals/` | offline tests: `run.py`, `package_cases.py` (build, skills, budget, work log), `cases.json`, `rules-cases.json`, `prepush-cases.json` |

## Not yet (later phases)

Not verified live: that Codex resolves `../../` paths from an installed plugin and lists all ten skills (see `intent/20261116-chatgpt-codex-support/spike.md`). Facts above are from Codex 0.169.0; a newer Codex may change hook trust, the skill list budget or the `apply_patch` input.

## Changelog

- 0.1.0: gates for Codex (deny instead of ask, `apply_patch` paths, approval token), rules, config template, pre-push hook, offline evals.
- 0.2.0: the package is complete: skills generated with Codex wording, Codex-own `ship-init` and `ship-doctor`, `agents/openai.yaml`, description budget check, policy copy with the tools table, work log writer and hooks, `AGENTS.md.template`; plugin name is `gdv-ai-kit`.
- 0.2.1: the policy table follows the C1 decision: class A and B with training off, class C never (was: class A only).
- 0.2.2: work log fixes: `level()` also reads AGENTS.md; a stop that re-measures a guessed session marks `tokens_basis: whole-session`; a second open log in one session is warned about and the already-open message says how to close it. Verifier agent and CONVENTIONS lose the `start_session` and `.claude/settings.local.json` wording; docs/parallel-sessions.md is in the package; the review gate message (block and ask) names `$gdv-ai-kit:ship-review`; `tokens_basis` is `whole-session` also when the start had no transcript.
- 0.2.3: rebuilt on the Claude plugin 1.3.0 (personal `mode` and `qc-url` in `AGENTS.local.md`, shown in the copied skills and CONVENTIONS). Two gaps: Codex `ship-doctor` does not warn about an invalid local `mode` (the copied CONVENTIONS says it does), and Codex `ship-init` does not ask for `mode` or `qc-url` (it writes the role only). 
- 0.2.4: the work log role regex no longer reads across lines (an empty `- role:` followed by `- mode: ...` returned the next line); ported from the Claude plugin 1.3.0 context hook.
- 0.3.0: model and effort config (Claude plugin 1.4.0): `kit-config.py`, `-m` and `-c model_reasoning_effort` on the verifier and review `codex exec` runs, a question in `ship-init`, a check in `ship-doctor`, `efforts` in the work log when the session file has it; eval cases for each.
