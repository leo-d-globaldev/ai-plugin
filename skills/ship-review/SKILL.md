---
name: ship-review
description: Use when work is ready to be reviewed - at the end of a work session before commit, "review trước khi commit", "review code này", "check my changes", "review trước khi push", or when a push was blocked because the commit has no review. Reviews the uncommitted work and the branch's commits in a fresh session against REVIEW.md, spec.md and plan.md, ranks findings Important or Nit with file and line, then on the developer's yes commits the work and records the review for that commit so the push gate opens. Never approves, merges or fixes by itself. Takes an optional intent ID or base branch and --mode=manual|semi-auto.
---

# ship-review

Stage 5 Deploy, play "AI in the PR review loop", run on the developer's machine **when the work of a session is done, before it is committed**: a review at push time comes too late, after many commits. The verdict is recorded for the commit in `.gdv/reviews/<sha>.md`; the hook (`${CLAUDE_PLUGIN_ROOT}/hooks/gates.py`) lets `git push` and PR/MR creation through only when the pushed commit has that file (a push that changes only intent and `.ai/` files needs none). Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

## Flow

Every stop after `work-log.py start` calls `work-log.py stop <ID> --outcome X` first (CONVENTIONS §4).

1. **Config and scope.** `## AI-KIT` section and the effective `mode` by CONVENTIONS §1 (argument, then `CLAUDE.local.md`, then `CLAUDE.md`); class C → stop. Base = the argument, else the main branch (`origin/HEAD`, else `origin/main`, `origin/master`, `main`, `master`; none → ask). The change = `git diff $(git merge-base BASE HEAD)` (the branch's commits **and** uncommitted changes) plus untracked files that belong to the work (`git status --short`; leave out build output and secrets). Nothing changed → say so and stop.
2. **Intent.** ID from the argument, the branch name (`PROJ-123-...`), or `links.md` that names this branch. Read `intent.md`, `spec.md`, the plan (CONVENTIONS §2). None → the review runs the Bugs, Security, Tests and Project passes only and says "no spec or plan".
   - `work-log.py start <ID> --skill ship-review` (no ID → the branch name with `/` replaced by `-`).
3. **Review in a fresh session in this same folder** (CONVENTIONS §6), so the verdict is not coloured by the author's reasoning. Its prompt holds: `REVIEW.md` of the repo (none → `${CLAUDE_PLUGIN_ROOT}/templates/REVIEW.md`), the acceptance criteria and the plan, the repo path, the base, how to get the change (step 1), and the result file `.gdv/tmp/review-ID.md`. Start it with the `model` and `effort` of `model-review` (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/kit-config.py" models`; CONVENTIONS §1 and §6) when set, and say in one line what you asked: `Review: model opus, effort high, from CLAUDE.md`, ending `not applied: REASON` when the host cannot apply it; then go on. It reads the change and the files around it, runs no command that changes anything, and writes findings in this form; the `Verdict:` line is plain text at the start of a line, no markdown around it:

   ```
   Verdict: no-important | important
   Important:
   - file:line — what is wrong — why it matters — passes: spec|bugs|security|tests|project
   Nit (at most 5):
   - file:line — ...
   Checked: passes run, criteria checked
   Not checked: what and why
   ```

   Read the result file. A finding without `file:line` is dropped. Check the `Verdict:` line is plain; fix its form (not its value) if it is not.
4. **Answer the developer.** Show Important first, then nits.
   - `important` → the developer fixes (back to the work, then `/ship-review` again) or accepts the findings explicitly; then the push gate **asks** a person and the lead decides.
5. **Commit and record.** Uncommitted work and the developer says yes (manual), or the run comes from `/ship-build` step 8 with the developer's yes → commit it on the change branch (never the main branch): `feat|fix(ID): TITLE`. semi-auto with nobody answering → do not commit; record nothing, stop (`blocked`). The work started from `/ship-build`: the intent status and the `links.md` branch line are already written and go into this commit.
   - Then write `.gdv/reviews/<HEAD sha>.md`: a first line `Review of SHA on BRANCH, DATE, base BASE`, then the result. `.gdv/` must be in `.gitignore`; missing → tell the person (or `/ship-init`) to add it; do not edit `.gitignore` here.
   - Append to `links.md`: `- repo: NAME · review: SHA · VERDICT · N important`. Committing it later (with the work-log record) needs no new review: the gate accepts documents committed after a reviewed commit.
   - New code commits after the review → run `/ship-review` again; commits of intent and `.ai/` files only keep the review.
   - Give a 5-line summary to paste into the PR/MR description. Comment on the ticket only when asked or `tracker-comments: on`.
6. `work-log.py stop <ID> --outcome done` (`gate` when the verdict is `important`; `gate` means only that, so metrics can count first-pass reviews).

## Rules

- The review never approves, merges or changes code; its only write to git is the commit of step 5, on the developer's yes. Fixes are the developer's next step (`/ship-build` or by hand).
- Do not raise a nit to Important. Do not invent findings: "no important findings" is a valid result.
- Code review on the git provider (managed Code Review, `claude-code-action`) can run as well; the lead's review of the MR/PR stays. This skill does not replace branch protection.

## Helper skills

When installed: `code-review` (or `engineering:code-review`) inside the review session for the Bugs and Security passes. Missing → run the passes as written.
