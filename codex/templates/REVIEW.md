# Review rules

<!--
Template for a project repo's REVIEW.md (playbook play "AI in the PR review loop"). Copy to the repo root, fill the <...> parts, delete every comment.
Read by $gdv-ai-kit:ship-review. The tech lead owns it. Keep it under one page: a point the lead keeps raising goes into Project checks; a check that never fires is removed.
-->

## Passes

<!-- $gdv-ai-kit:ship-review runs these in order on the diff of one change. -->
1. **Spec and plan:** each acceptance criterion in `spec.md` (or `intent.md`) is met by the diff; the diff follows `plan.md` (files, order); every departure from the plan is written in the plan.
2. **Bugs:** wrong conditions, unhandled empty or error cases, off-by-one, wrong units, races.
3. **Security:** secrets or tokens in code or logs, injection, missing auth or permission checks, unsafe input, personal data in logs.
4. **Tests and scope:** tests check the criterion, not the implementation; no test was weakened to pass; nothing changed outside the change.
5. **Project checks:** the list below.

## Important vs nit

- **Important:** would change a decision or break something. A criterion not met, a bug a user can hit, a security hole, a test changed only to pass, a change outside scope.
- **Nit:** wording, naming, style, small simplification, anything a linter catches.
- Unsure: it is a nit. Every finding has `file:line` and one sentence on why it matters. No location, no finding.
- At most 5 nits; the rest are counted in one line.

## Project checks

<!-- Rules specific to this repo. Mark each Important or nit. 3 to 8 lines. -->
- `<Every new endpoint checks permission X>` (Important)

## Skip

- `<generated code, lockfiles, vendored paths>`
