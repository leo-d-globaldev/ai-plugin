---
name: ship-test
description: Use for QC work on a change - "viết test case", "test ticket PROJ-123", "chạy test", "QC cần làm gì", "báo bug", "regression test". With no argument lists what QC should do now, read from the intent folders and git (or the ticket status). --plan writes tests.md and e2e tests from the acceptance of spec.md, intent.md or the ticket; --run runs the cases (browser tool for UI) and records results; --bug turns a failed case into a failing test and a bug intent for the developer. Takes an optional ID, --plan, --run, --bug and --mode=manual|semi-auto.
---

# ship-test

Stage 4 Test for QC: QC owns what "passes" means (the Acceptance) and keeps the feedback loop honest. Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

Every stop after `work-log.py start` calls `work-log.py stop <ID> --outcome X` first (CONVENTIONS §4): `gate` waiting for a person, `blocked` missing input, `failed`, `done`. QC documents (`tests.md`, e2e tests) are committed on a `qc/ID` branch (or the docs repo); a push of intent and `.ai/` files only needs no AI review, e2e test code does.

## No argument: what should QC do now?

Read every `<intent-home>/*/intent.md` front matter on the main branch (`git fetch` first when there is a remote), `tests.md`, `links.md` and git, and answer with one list, most urgent first. The status a developer writes lives on their branch until the merge; on main read the branch in `links.md` (`git branch -r --merged`) for the truth:

| State | QC does |
|---|---|
| `spec.md` approved (or the intent/ticket has acceptance) and no `tests.md` | `/ship-test ID --plan` |
| The change is ready for QC and its latest code has no run in `tests.md` | `/ship-test ID --run` |
| The latest run has a `fail` without a bug raised | `/ship-test ID --bug` |
| A bug intent is `merged` and has no regression case | add it: `/ship-test BUG-ID --plan` |
| A parent intent (other intents name it in `parent:`) | its line shows the children: `merged` X of N, with owner and status of the rest. Every child merged → the parent is ready for its end-to-end run: `/ship-test PARENT --run` (and `--plan` first when it has no `tests.md`). A child's own cases test that child only |

"Ready for QC" comes from `qc-signal` (CONVENTIONS §1): `merge` → the branch in `links.md` is merged into the main branch (`git branch -r --merged`) or the intent says `merged`; `ticket-status:NAME` → `get-item` shows that status. Multi-repo projects default to the ticket status. Say for each line why it is there. Ticket keys the person gives (or pastes from their tracker board, e.g. the "Ready for QC" column) with no intent folder yet → list them as `--plan` work: there is no tracker search, only `get-item` per key.

**Writing `merged`.** This mode writes one thing: an intent whose branch git shows merged into the main branch, and whose status is before `merged`, is set to `status: merged` (on the main branch, in a commit `docs(ID): merged` after the person's yes; semi-auto: list them and leave them). It is the only skill that sets `merged`; `/ship` and QC rely on it. A parent intent has no branch: it is set to `merged` when every child is `merged`, in the same commit.

## --plan

1. `work-log.py start <ID> --skill ship-test`. No `intent.md` and the ID is a ticket key → `get-item` and write a minimal intent as `/ship-build` step 2 does (ticket rule, CONVENTIONS §2), so the work shows in `/ship` and the session context. Source of acceptance, in order: `spec.md` Acceptance, `intent.md` Acceptance, the ticket. None → ask the BA (manual) or write the question into the intent's Open questions (semi-auto) and stop (`blocked`).
2. Write `<intent-home>/<ID>/tests.md` from `${CLAUDE_PLUGIN_ROOT}/templates/intent/tests.md`: at least one case per acceptance row, plus the edges a tester would try (empty, too long, no permission, slow network, two users at once). Mark each case `e2e` (automated) or `manual`.
3. Automated cases: write them in the repo's e2e framework (find it in `CLAUDE.md` or the project; none → keep them manual and say so). Multi-repo: the e2e repo or the docs repo, as `CLAUDE.md` says.
4. A case that shows the acceptance is ambiguous → flag it to the BA; do not guess the expected result.
5. `work-log.py stop <ID> --outcome done`. Commit when QC agrees: `test(ID): test cases` on the `qc/ID` branch.

## --run

1. `work-log.py start <ID> --skill ship-test`. Which build: the merged commit, or the QC environment (`qc-url` in the `## AI-KIT` section, else ask the person).
2. Run the e2e cases with the project's command; run UI and manual cases through the browser tool, step by step, taking a screenshot for each failure. Never use real customer data (class B) or production.
3. Append a run block to `tests.md`: case, `pass | fail | not run`, note, screenshot path. Set intent `status: testing`.
4. All pass → say the change can be accepted; setting `done` (and closing the ticket) is a person's decision (CONVENTIONS §5). Some fail → suggest `--bug` for each.
5. `work-log.py stop <ID> --outcome done` (`gate` when a case failed); comment the run summary on the ticket only when asked or `tracker-comments: on`.

## --bug

1. For one failed case (or a bug a person reports): `work-log.py start <BUG-ID> --skill ship-test`, BUG-ID = the bug ticket key, else `YYYYMMDD-bug-slug`.
2. Write `<intent-home>/<BUG-ID>/intent.md` with `source: bug`, `status: approved`, `approved: "QC NAME DATE"` (bug rule, CONVENTIONS §2: QC approves the bugs QC raises), steps to reproduce, expected, actual, the case and run it came from, and a link to the parent intent.
3. Write the failing automated test that reproduces it when the repo is reachable, on a branch `BUG-ID-short-title` cut from the main branch; run it, show it fails for the reported reason, commit it alone there. The developer continues on that branch. The developer then runs `/ship-build BUG-ID`; the test file is locked during the fix.
4. Record the bug ID in the run block. Raising a bug on the customer's tracker happens only when the person asks.
5. `work-log.py stop <BUG-ID> --outcome done`.

## Rules

- QC never edits product code to make a case pass; the test is the contract.
- A production bug that is fixed gets a regression case (and, when the repo has `evals/`, an eval when an AI mistake caused it).

## Helper skills

When installed: `engineering:testing-strategy` for --plan.
