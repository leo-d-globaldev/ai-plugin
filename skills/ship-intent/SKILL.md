---
name: ship-intent
description: Use when someone has a new idea, request, feature, problem or ticket to capture before any design or code - "có ý tưởng mới", "khách hàng muốn thêm tính năng", "write up this requirement", "tạo yêu cầu từ ticket PROJ-123". Brainstorms with the originator and writes intent.md (what is wanted, why, constraints, draft acceptance, open questions) in the project's intent home, then asks the PO or BA to approve it. For BA, PO and PM; works on claude.ai with a Git connector too. Takes an optional ticket KEY or text and --mode=manual|semi-auto.
---

# ship-intent

Stage 1 Plan, play "Capture as intent.md". Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

## Flow

Every stop after `work-log.py start` calls `work-log.py stop <ID> --outcome X` first (CONVENTIONS §4): `gate` waiting for a person, `blocked` missing input, `failed`, `done`.

No shell (claude.ai, Cowork): skip the `work-log.py` steps and say so in one line.

1. **Config.** `## AI-KIT` section and the effective `mode` by CONVENTIONS §1 (argument, then `CLAUDE.local.md`, then `CLAUDE.md`); class C → stop. Find the intent home (CONVENTIONS §2). A separate docs repo that is not reachable → say where to clone it, or how to reach it through the Git connector, and stop.
2. **Source.**
   - A ticket key → `get-item`; ID = the key; `source: ticket`. An intent for that ID already exists → open it and continue it instead of writing a new one. A ticket that is already accepted for work follows the ticket rule of CONVENTIONS §2 (`status: approved`, `approved: "ticket KEY"`): skip the approval of step 5 and say so; write a draft only when the ticket is itself a raw request still to be decided.
   - Text, a file or a conversation → ID = `YYYYMMDD-short-slug`; `source: idea`.
   - `work-log.py start <ID> --skill ship-intent`.
3. **Brainstorm** with the originator, a few questions at a time, until these are clear: the outcome wanted, why (who is affected, how often, what it costs today), constraints (deadline, systems that must not change, compliance, data class), how we would know it worked, what is out of scope. Do not design the solution here. Things nobody can answer now go to Open questions with an owner.
   - semi-auto: no questions; write what the source says and list every gap in Open questions.
4. **Write** `<intent-home>/<ID>/intent.md` from `${CLAUDE_PLUGIN_ROOT}/templates/intent/intent.md`, `status: draft`. Keep it to about half a page in the originator's own words. Multi-repo project: fill `repos:` when it is already clear.
5. **Approval.** Show it and ask the PO/BA who owns the outcome: approve, change, or drop. Only that person's yes in chat sets `status: approved` and `approved: "NAME (ROLE) DATE"`. The originator is the approver → still ask in one line.
6. **Commit** when the person agrees: `docs(ID): intent` on a `docs/ID` branch (CONVENTIONS §2: a push that holds only intent and `.ai/` files needs no AI review), or the docs repo's main branch when the project allows it. People without Git: write through the Git connector, which opens a PR.
7. `work-log.py stop <ID> --outcome done` (`gate` when waiting for approval). Next step, in one line, once the intent is approved: `/ship-spec ID` (project-based) or `/ship-build ID` (small change, no spec needed). Still draft → name who approves it.

## Helper skills

When installed: `product-management:write-spec` or `superpowers:brainstorming` for step 3.
