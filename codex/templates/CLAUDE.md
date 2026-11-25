# <Project name>

<!--
Template for a project repo's CLAUDE.md (playbook play "The CLAUDE.md"). Keep the result under one page.
How to use: $gdv-ai-kit:ship-init runs the analysis /init would, then cuts it down to these sections. Delete every comment.
Rule: when Claude gets the same thing wrong twice, the correction goes into "Mistakes Claude often makes".
-->

One sentence: what the project is and who uses it.

## Commands

<!-- Exact commands, each with what a healthy run prints (the feedback loop depends on it). -->
- Build: `<cmd>`
- Test: `<cmd>` (healthy: `<N passed, 0 failed>`); one file: `<cmd> <path>`
- Lint: `<cmd>` (healthy: no output)
- Run: `<cmd>` (port; env file name, never the values)

## Conventions

<!-- Only rules a linter cannot enforce. 5 to 8 lines. -->
- `<language, framework, version>`
- `<naming, layout, error handling, logging>`
- Every behavior change has a test in `<path>`

## Architecture

- `<folder>`: `<what it holds>`
- Data flow: `<A -> B -> C>`

## Mistakes Claude often makes

- `<Does X; should do Y>`

## Verify before you say done

1. Run the test and lint commands; show the output.
2. Check each acceptance criterion in `spec.md` (or `intent.md`) against the diff.
3. Report what you ran, what passed, what you did not check.

## Never without a human

- Merging, deploying to production, deleting data or branches, sending anything to the customer
- Reading or printing secrets (`.env`, keys, tokens); use their names only

<!-- Docs repo of a multi-repo project only: list the code repos here, one line each.
## Repos
- backend: git@host:group/backend.git (usual path ../backend)
-->

## AI-KIT

<!-- Read by the gdv-ai-kit skills (CONVENTIONS.md section 1). An argument on a command still wins. -->
- mode: manual
- intent-home: ./intent
- adapter: none
- data-class: A
- qc-signal: merge
- tracker-comments: off
- review-gate: block        # block | ask | off
- qc-url:                    # QC environment, if any (a person may override it in AGENTS.local.md)
- worklog: remind
# Model and effort per stage, MODEL/EFFORT (empty = the session's own); a person may override each in AGENTS.local.md. Optional:
# - model-easy: sonnet/medium
# - model-medium: sonnet/high
# - model-hard: opus/high
# - model-verify: sonnet/medium
# - model-review: opus/high
