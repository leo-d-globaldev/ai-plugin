# Evals of this project (written by /ship-init)

Tests of this project's AI setup: `CLAUDE.md`, `.claude/skills`, `.claude/agents`. The runner (`run.py`, `on-change.sh`) comes from the gdv-ai-kit plugin; the cases are yours.

- `hook-cases.json`: offline cases for the hard-gate hook (format: the plugin's `evals/hook-cases.json`). Starts empty.
- `tasks/<id>/`: one task per folder: `eval.json` (prompt), `fixture/` (files the run starts with), `check.sh` (exit 0 = pass). Starts empty. Add one for every production bug.
- `thresholds.json`: minimum pass rate per kind.

Run locally: `AI_DLC_PLUGIN_DIR=<path to a clone of the plugin repo> evals/run.py --kind hook`. Task evals call `claude -p` and cost money. CI: the `ai-dlc-evals` job in `.gitlab-ci.yml`; without its variables it only warns. Details and the case format: the plugin's `evals/README.md`.
