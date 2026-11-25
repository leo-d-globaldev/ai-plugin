# Several tickets at once (parallel sessions)

Playbook play "Parallel sessions and subagents". Goal: two or three changes move at the same time without overwriting each other, and review still keeps up. Owner: the developer.

## How

1. One session per ticket, each in its own worktree: in the repo root run `claude --worktree PROJ-123` (and `claude --worktree PROJ-124` in another terminal). Each worktree is its own checkout and branch.
2. In each session say "làm ticket PROJ-123" (or `$gdv-ai-kit:ship-build PROJ-123`). Each ticket gets its own `intent/<ID>/`, its own plan, its own work-log records and its own review; the gates work per session.
3. Tickets that change the same files do not run in parallel: run them one after the other in one session. The "Files that change" table of each plan shows the overlap.
4. Push each branch after its `$gdv-ai-kit:ship-review`; the lead merges by the normal PR/MR flow.
5. After the merge: `git worktree remove .claude/worktrees/PROJ-123` and delete the branch. Never remove a worktree that holds unreviewed work.

## How many

Start with **2**. Go to 3 only after a day in which every change was reviewed the same day. More sessions than you can review only moves the queue to the reviewer.

## What worktrees do not solve

- Shared state outside git (a local database, ports, `.env`, caches): give each worktree its own, or run those tickets one at a time.
- Merge conflicts between branches that edit the same file.
- Review capacity.

## Multi-repo changes

A ticket that touches backend and web **and one person builds both**: one intent in the docs repo, one session per repo (each in that repo's worktree), one plan per repo (`.ai/plans/<ID>.md`). `links.md` in the intent folder lists the branch and review of each repo.

**Different people build the parts:** split it at `$gdv-ai-kit:ship-spec` into a parent intent and child intents (`ID-a`, `ID-b`), one owner each (CONVENTIONS §2, split intents). The parent spec fixes the contracts between the systems first; each child has `parent`, `owner`, `repos` and `depends-on`. Each owner runs `$gdv-ai-kit:ship-build` on their child; a child whose dependency is not merged builds against the contract with a stub, or waits. `$gdv-ai-kit:ship-test` sets the parent `merged` when every child is, then QC runs the parent's end-to-end cases.
