---
id: <ID>
repo: <repo name>
complexity: easy | medium | hard
approved: ""                # "NAME DATE": the session owner's yes; empty = draft, no code yet
---

# Plan: <ID> <title>

<!--
Playbook play "Claude Code plan mode as the default starting point". Drafted in plan mode, written here after the session owner approves it, before any code.
Where: <intent-home>/<ID>/plan.md when the intent lives in this repo; .ai/plans/<ID>.md in each code repo when the intent lives in a docs repo.
easy: optional (a few lines). medium: required. hard: required, Risks not empty.
Iterate until an engineer who never saw the conversation could implement the change from this plan alone.
When the implementation departs from the plan, update this file in the same commit.
-->

**Intent:** <path to intent.md>@<commit> · **Spec:** <path or "none">

## Criteria covered

- A1: <text>

## Files that change

| File | Change | Why |
|---|---|---|
| `<path>` | add / edit / delete | <reason> |

## Order of work

1. <smallest step first; each step leaves the repo working>

## Risks

<!-- What could break, which step is riskiest, how you would notice. -->
- <risk>: detected by <test>; mitigation: <...>

## Options not taken

- <option>: <why not>

## Proof

| Criterion | Test or command | Expected |
|---|---|---|
| A1 | `<cmd>` | <result> |

## Out of scope

- <...>
