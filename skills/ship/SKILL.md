---
name: ship
description: One entry point for the GDV AI-KIT when the person does not know or remember which step to run - "/ship làm tiếp", "/ship tôi muốn thêm tính năng X", "/ship PROJ-123", "what should I do next", "bước tiếp theo là gì". Reads the person's words, their role and the state of the intent folders, says which skill fits and why, then runs it (in manual mode after one yes). Takes optional free text, an optional KEY and --mode=manual|semi-auto.
---

# ship

The fallback entry point. Most of the time the right skill loads by itself from what the person says; `/ship` is for when it does not, or when the person prefers one command. Read `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md` first.

## Flow

1. **Read** the `## AI-KIT` section (class C → stop), the role in `CLAUDE.local.md` (none → treat as `all` and suggest `/ship-init` once) and the effective `mode` by CONVENTIONS §1 (argument, then `CLAUDE.local.md`, then `CLAUDE.md`), and the open intents (front matter of `<intent-home>/*/intent.md`, plus `tests.md` and `links.md`). Read-only so far.
2. **Pick** the skill from the person's words first, the state second:

   | Words or state | Skill |
   |---|---|
   | new idea, request, "khách muốn", a ticket with no intent and no code planned | `ship-intent` |
   | intent approved, project needs a spec; "spec", "thiết kế", "phân tích" | `ship-spec` |
   | a ticket key to implement, "làm", "fix", "implement", "làm tiếp" on an intent in `approved`..`building` | `ship-build` |
   | "review", "push", "PR", "MR", an intent in `review` without a review of HEAD | `ship-review` |
   | role QC, "test", "QC", "bug", an intent in `specified`, `merged` or `testing` | `ship-test` (no argument lists the work) |
   | role lead: a plan waiting for its owner (`plan.md` with `approved: ""`), a review with `important` before a push, a lead task (system design, a spike) | that intent's owner runs `ship-build`; the lead's own task → `ship-build`; the MR/PR review is on the git provider |
   | role pm: "báo cáo", "số liệu", "metrics", "tiến độ" | no skill: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/metrics.py" --md` and `work-log.py report --md`, and show the list of open intents with status |
   | a Sentry URL, an alert, a metric breach | `ship-maintain` (tell the person to type it: `/ship-maintain SIGNAL`) |
   | setup, "cài đặt", no `## AI-KIT` section | `ship-init` (tell the person to type `/ship-init`) |
   | "không chạy", errors from the kit | `ship-doctor` |

   Several fit (e.g. `specified` fits both `ship-build` and `ship-test`) → prefer the person's role (`dev`/`lead` → build/review, `qc` → test, `ba`/`po` → intent/spec, `pm` → the report row). Still several → list two or three options, each with one line on what it does, the first being your pick.
3. **Say** in one line: `→ /ship-build PROJ-123: the intent is approved and has no plan yet.`
4. **Run** it: manual → after the person's yes; semi-auto → at once. Pass the key and `--mode` through. `ship-init` and `ship-maintain` cannot be started by the model (`disable-model-invocation`): name the command for the person to type, do not do their work yourself. Nothing fits → say what you read and ask one question.

## Rules

- `/ship` itself changes nothing; the skill it runs does, under that skill's own rules and gates.
- It never skips a gate because the person asked for "the next step".
