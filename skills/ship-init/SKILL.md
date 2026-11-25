---
name: ship-init
description: Sets up a project repo for the GDV AI-KIT, once per repo and once per person - writes or trims CLAUDE.md, adds REVIEW.md, chooses the intent home (folder, sparse checkout or separate docs repo for monorepos and multi-repo projects), the data class, the tracker adapter and the QC signal, wires the docs repo into the session, and saves the person's role. Invoked as /ship-init; writes only after a yes.
disable-model-invocation: true
---

# ship-init

First command in a repo. Playbook plays it sets up: "The CLAUDE.md", "Capture as intent.md" (the intent home), "Hooks as approval gates" (they ship with the plugin). Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first. It writes nothing until the person has seen the list of changes and said yes.

## Questions (one at a time, each with the default you suggest)

Ask one question per message, in the order below, and wait for the answer before the next. Show the default and, for a choice, the options with one line each (use the question tool when there is one). Skip a question you can already answer from the repo, `CLAUDE.md` or an earlier answer, and say so in a short line. Never post the whole list. The person may answer "default" or "ok" for any of them; a later answer may change an earlier one (go back, do not restart). Question 2 answered C → stop as described there.

1. **Your role(s) here:** po, ba, dev, lead, qc, pm (comma list) or all. Saved in `CLAUDE.local.md` only.
2. **Data class** of this project under the customer contract: A, B or C (`${CLAUDE_PLUGIN_ROOT}/docs/platform.md`, section Data classes). Unsure → B, and tell the person to confirm with the delivery lead. C → write only the section with `data-class: C` and stop: read no other file, analyse nothing, no other setup.
3. **Project shape** (suggest from what you see: one repo, a monorepo with many modules, or this repo is one of several):
   - one repo → `intent-home: ./intent`;
   - large monorepo → `./intent` plus a sparse checkout for non-developers (`git sparse-checkout set intent/`), or a separate docs repo when BA/QC/PM should not clone the code;
   - several repos → a separate docs repo (`PROJECT-docs`): ask its git URL and where it is cloned (default `../PROJECT-docs`).
4. **Tracker:** jira, windshift or none; whether skills may comment on tickets without asking (`tracker-comments`, default off); one ticket key to test the connection with.
5. **QC signal:** `merge` (default for one repo) or `ticket-status:NAME` (default for several repos), e.g. `ticket-status:Ready for QC`.
6. **Mode:** manual (default) or semi-auto for the project (`CLAUDE.md`); then **your own mode here**: the same as the project (default) or the other one, saved in `CLAUDE.local.md` only. **Work log:** remind (default), strict or off.
7. **Main branch**: the gates treat `main`, `master`, `develop` and `trunk` as main branches. Another name (e.g. `release`) → add a `bash_gates` entry for it in `.claude/gdv-gates.json`.
8. **Review gate** for pushes without an AI review of the pushed commit: `block` (default) or `ask` (the person may push after a prompt; suggest it for a team just starting). Pushes of intent and `.ai/` files only are never gated.
9. **QC environment** URL, when there is one (`qc-url`): for the whole team (`CLAUDE.md`, default) or only for you (`CLAUDE.local.md`).
10. **Model and effort** (CONVENTIONS §1, section Model and effort; optional): for a change rated easy, medium or hard (the session that builds), for the verifier and for the review. Suggest `easy sonnet/medium`, `medium sonnet/high`, `hard opus/high`, `verify sonnet/medium`, `review opus/high`; the person may change any, or answer `default` to leave all to the session. Then: for the whole team (`CLAUDE.md`, default) or only for you (`CLAUDE.local.md`). Say the allowed values (MODEL `opus`, `sonnet`, `haiku` or a full id; EFFORT `low|medium|high|xhigh|max`), that a session cannot raise a host-started session above its own model, and that running `/ship-init` again changes them.

## Changes it proposes (shown as a list, then one yes)

- **CLAUDE.md**: missing → analyse the repo as `/init` would (build, test, lint commands with a healthy output, conventions, architecture, the mistakes to avoid) and write it from `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`, under one page. Present → keep it, only add or update the `## AI-KIT` section (with the `model-*` lines of question 10 when they are for the team); an old `## AI-DLC defaults` section is replaced (its `mode`, `adapter` and `worklog` carry over).
- **REVIEW.md** at the repo root from `${CLAUDE_PLUGIN_ROOT}/templates/REVIEW.md`, when missing.
- **Intent home**: create `intent/` with a one-line README (or nothing, for a docs repo). Docs repo: add its path to `additionalDirectories` in `.claude/settings.local.json` (each person clones it in their own place) so sessions in this repo can read it; never a submodule. In the docs repo's `CLAUDE.md`, a `## Repos` list maps each repo name to its git URL and usual local path.
- **.gitignore**: `.gdv/` (local state: session files, bug lock, reviews). `.ai/` is committed (work log, plans in multi-repo).
- **Optional git pre-push hook** for pushes made outside Claude: `scripts/pre-push.sh` copied to `.git/hooks/pre-push` (local, per clone; ask separately).
- **Optional evals CI job**: `templates/gitlab-ci.yml` appended to `.gitlab-ci.yml` (it checks out the plugin and runs the plugin's `evals/on-change.sh` against the project's `evals/`), and `templates/evals/` copied to `evals/` (ask separately; see `${CLAUDE_PLUGIN_ROOT}/evals/README.md`). The project's `.gitlab-ci.yml` needs a `test` stage; missing → say so.
- **Optional auto-compact threshold** (ask separately): long runs fill the context; suggest compacting at a moderate level, e.g. `"env": {"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70"}` in `.claude/settings.local.json` (personal), or `/autocompact` where Claude Code has it.
- **CLAUDE.local.md**: `## AI-KIT me` with `- role: ...`, and `- mode: ...` `- qc-url: ...` and the `model-*` lines only when the person chose a personal value in questions 6, 9 and 10 (add `CLAUDE.local.md` to `.gitignore`).

## After writing

- Check the tracker connection with one `get-item` on the key from question 4 (skip when `adapter: none`). Failure → say how to sign in (adapter file) and go on.
- Run the checks of `/ship-doctor` and show the table.
- Say how to start, in two lines for the person's role: dev `/ship-build PROJ-123` (or just "làm ticket PROJ-123"); qc `/ship-test`; ba/po `/ship-intent`; anyone `/ship`.
- Commit nothing; suggest the commit `chore: set up GDV AI-KIT` for the person to make.
