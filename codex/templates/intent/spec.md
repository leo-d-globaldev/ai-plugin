---
id: <ID>
approved: ""                # "NAME (PO/BA) DATE" once approved; the intent's status carries the stage
---

# Spec: <title>

<!-- Playbook play "Requirements and design": requirements and design in one session, from the approved intent.md, constrained by the organization's policy skills. The PO reviews it; nobody writes it by hand. -->

## Requirements

| # | Requirement | From intent |
|---|---|---|
| R1 | <...> | What we want, line 1 |

## Acceptance

<!-- What QC turns into tests.md. Each line testable, with data. -->
| # | Given | When | Then |
|---|---|---|---|
| A1 | <state> | <action> | <observable result> |

## Design

<!-- Components touched, API contracts, data model changes, UI notes; options considered with the one chosen and why. Per repo when several. -->

### Repos touched

- `<repo>`: <what changes>

## Breakdown

<!-- Only when the change is split into child intents (CONVENTIONS §2, split intents). The children's intent.md front matter is the truth; this table is for people. Delete the section otherwise. -->

| Child | System / repo | Owner | Depends on | Contract it provides or uses |
|---|---|---|---|---|
| ID-a | backend | NAME (dev) | - | provides: POST /claims/{id}/status |
| ID-b | web | NAME (dev) | ID-a, or none when built against the contract | uses: POST /claims/{id}/status |

## Flagged concerns

<!-- Points an analyst would have escalated: security, compliance, UX, performance, data. Each with the policy owner who resolves it and the resolution. Engineering does not start while one is open. -->
| # | Concern | Policy / owner | Resolution |
|---|---|---|---|
| C1 | <...> | <skill or person> | open |

## Open questions

- <question> (owner: <...>)
