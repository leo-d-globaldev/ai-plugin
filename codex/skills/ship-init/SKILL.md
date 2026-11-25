---
name: ship-init
description: Sets up a project repo for the GDV AI-KIT on Codex, once per repo and once per person - writes the AI-KIT section of CLAUDE.md, the role in AGENTS.local.md, REVIEW.md, the intent home, the data class, the Codex config and the git pre-push hook. Run only when the person types it; it writes project config.
---

# ship-init (Codex)

First command in a repo, run by the person only. Read `../../CONVENTIONS.md` first. It writes nothing until the person has seen the full list of changes and said yes. Paths `../../X` are relative to this folder; commands run in the repo.

## Questions (one at a time, each with the default you suggest)

Skip a question the repo already answers (an existing `## AI-KIT` section).

1. **Your role(s):** po, ba, dev, lead, qc, pm (comma list) or all. Saved in `AGENTS.local.md` only (`## AI-KIT me`, `- role: qc`).
2. **Data class** under the customer contract: A, B or C (`../../docs/platform.md`). Unsure → B and tell the person to confirm with the delivery lead. C → write only `data-class: C`, tell the person Codex must not be used here, stop. On Codex, class A and B are allowed only with model training turned off for the account; class C never (see "Tools per data class" in the Codex README).
3. **Project shape:** one repo (`intent-home: ./intent`), a monorepo, or several repos (separate docs repo).
4. **Tracker:** jira, windshift or none; `tracker-comments` (default off). A tracker needs its MCP server in `~/.codex/config.toml` (see `config.toml.template`).
5. **QC signal, mode, work log, review gate:** as in CONVENTIONS §1. Work log `strict` is not enforced on Codex (edits arrive as `apply_patch`): it runs as `remind`.
6. **Main branch** name, if not main, master, develop or trunk.
7. **Model and effort** (CONVENTIONS §1, section Model and effort; optional): for a change rated easy, medium or hard (the session that builds), for the verifier run and for the review run. Value `MODEL/EFFORT` (either part may be left out; empty or `default` = what Codex would use). `codex exec` gets them as `-m MODEL` and `-c 'model_reasoning_effort="EFFORT"'`; the model ids and the efforts a model accepts depend on the account, so ask the person for ids they use (`codex` shows them in `/model`); do not invent ids. Then: for the whole team (`CLAUDE.md`, default) or only for you (`AGENTS.local.md`). Running `$gdv-ai-kit:ship-init` again changes them.

## Changes it proposes (a list, then one yes)

- **CLAUDE.md**: the `## AI-KIT` section, with the `model-*` lines of question 7 when they are for the team (Codex reads it because `project_doc_fallback_filenames` lists CLAUDE.md; step below). Missing file → write it from `../../templates/CLAUDE.md`, under one page.
- **AGENTS.md** at the repo root, when missing, from `../../AGENTS.md.template` (a pointer to the AI-KIT section and the skills).
- **AGENTS.local.md** with `## AI-KIT me`, the role, and the `model-*` lines only when the person chose personal values in question 7; add `AGENTS.local.md` and `.gdv/` to `.gitignore`. `.ai/` is committed.
- **REVIEW.md** from `../../templates/REVIEW.md`, when missing. **Intent home**: `intent/` with a one-line README.
- **Codex config** (`~/.codex/config.toml`, personal): merge `../../config.toml.template` (the `project_doc_fallback_filenames` line). Show the diff, never overwrite other keys.
- **Rules**: copy `../../rules/gdv.rules` to `~/.codex/rules/gdv.rules` (prompts for `git push`, `terraform apply`, `kubectl apply`, `helm upgrade`). Ask separately.
- **Git pre-push hook** (second layer for the review gate): copy `../../pre-push.sh` to `.git/hooks/pre-push`, `chmod +x`. Ask separately.

## After writing

1. Tell the person to open `/hooks` in Codex and **trust** the plugin's hooks. Until they do, the gates and the work log do nothing; `$gdv-ai-kit:ship-doctor` checks this.
2. Run `$gdv-ai-kit:ship-doctor` and show its table.
3. Say what was not done and why. Never push, never edit a file the person did not see in the list.
