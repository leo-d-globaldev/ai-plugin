---
name: ship-spec
description: Use when an approved intent needs requirements and design before engineering plans it - "viết spec", "phân tích yêu cầu và thiết kế", "turn this intent into a spec", "design the solution for PROJ-123". Produces spec.md in one session (requirements, testable acceptance in Given When Then, design per repo, flagged concerns with their policy owner, open questions), guided by the organization's policy skills, then asks the PO or BA to approve it. Takes an intent ID and --mode=manual|semi-auto.
---

# ship-spec

Stage 2 Design, play "Requirements and design": requirements and design in one working session, constrained by the organization's skills. The PO reviews the spec; nobody writes it by hand. Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

## Flow

Every stop after `work-log.py start` calls `work-log.py stop <ID> --outcome X` first (CONVENTIONS §4): `gate` waiting for a person, `blocked` missing input, `failed`, `done`.

1. **Config and intent.** `## AI-KIT` section and the effective `mode` by CONVENTIONS §1 (argument, then `CLAUDE.local.md`, then `CLAUDE.md`); class C → stop. Open `<intent-home>/<ID>/intent.md`. No ID → list intents with `status: approved` and ask. `status: draft` → it needs approval first (who: CONVENTIONS §2); stop (`blocked`).
   - `work-log.py start <ID> --skill ship-spec`.
2. **Context.** Read the code areas the intent touches (in a multi-repo project: the repos in `repos:`, at the paths listed under `## Repos` in the docs repo's `CLAUDE.md` or reachable through `additionalDirectories`; say which were not read). Load the policy skills that apply: `policy-client-data` always; any other installed organization skill for security, API design, UX or brand whose description matches.
3. **Write** `<intent-home>/<ID>/spec.md` from `${CLAUDE_PLUGIN_ROOT}/templates/intent/spec.md`:
   - Requirements, each traced to a line of the intent.
   - Acceptance: Given / When / Then with concrete data. QC builds tests from this table, so each row must be checkable.
   - Design: components, API contracts, data model, UI notes; options considered and the one chosen. Multi-repo: one subsection per repo, and fill `repos:` in the intent.
   - Flagged concerns: everything an analyst would escalate (security, compliance, personal data, performance, UX, a missing decision), each with the policy or person who owns it. Engineering does not start while one is open.
   - Open questions carried from the intent, answered or still open.
   - Breakdown, when the work is large or spans systems built by different people: split it into intents that one person can own end to end (one branch, one plan). Work that two people would do in parallel becomes two intents (`ID-a`, `ID-b`), never two branches on one intent: the status of an intent lives on its owner's branch and two branches would conflict on it (CONVENTIONS §2, split intents). Before splitting, the Design must state every **contract between the parts** (endpoint, payload, event, schema, error cases), because each owner builds against it. Then:
     - write each child's `intent.md` from the template with `parent: ID`, `owner:` (ask who; semi-auto: leave it empty and list it in Open questions), `repos:`, `depends-on:` (the children it needs merged first; none when both sides build against the contract), `status: specified` and `approved:` copied from the parent spec's approval once it is given, and Acceptance = the parent's rows that child delivers;
     - add a `## Breakdown` table to the parent `spec.md`: child, system, owner, depends-on, contract it provides or uses;
     - check that `depends-on` has no cycle and names only children of this parent or existing intents.
4. **Review with the PO/BA.** Concerns first. The PO resolves each with its owner; write the resolution. Then ask for approval. Only a person's yes in chat sets the spec's `approved: "NAME DATE"` and the intent's `status: specified`. semi-auto: write the spec, list the concerns, stop at approval (`gate`); the intent stays `approved` and `/ship-build` refuses a spec whose `approved:` is empty.
5. Commit when the person agrees: `docs(ID): spec`, on a `docs/ID` branch or the docs repo, as for the intent.
6. `work-log.py stop <ID> --outcome done|gate`. Next, in one line: QC `/ship-test ID --plan` and Dev `/ship-build ID`, in parallel (QC writes cases while Dev builds).

## Helper skills

When installed: `engineering:system-design` and `engineering:architecture` for the Design section, `design:ux-copy` for UI text.
