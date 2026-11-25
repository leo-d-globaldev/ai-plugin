---
id: <PROJ-123 or YYYYMMDD-slug>
title: <one line>
source: idea | ticket | signal | bug
ticket: <PROJ-123, optional>
repos: [<repo>, <repo>]
parent: ""            # child of a split intent: the parent ID
depends-on: []        # intents whose merge this one needs first (a contract, an API)
owner: ""             # who builds it: NAME (role); one owner per intent
status: draft
approved: ""
---

# <title>

<!-- Playbook play "Capture as intent.md": what is wanted, why, and under which constraints, in the originator's own words. Half a page. -->

## What we want

<!-- The outcome, from the user's side. -->

## Why

<!-- The problem or the signal behind it; who is affected; how often. -->

## Constraints

<!-- Deadline, compliance, systems that must not change, budget, data class. -->

## Acceptance (draft)

<!-- How we will know it worked. Testable lines; $gdv-ai-kit:ship-spec turns them into Given/When/Then. -->
- <...>

## Out of scope

- <...>

## Open questions

<!-- Each with who answers it. Empty when none. -->
- <question> (owner: <PO|BA|customer>)
