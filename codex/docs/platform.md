# Platform setup for the GDV AI-KIT

Owner: GlobalDev platform / IT, with the delivery and security lead. This is the part of the playbook that answers a customer's question "how is my code handled by AI?" (`client-ai-statement.md` is the one-page answer). Roll out in this order; each step stands alone.

## 1. Data classes (per project, from the contract)

| Class | The customer allows | Setup |
|---|---|---|
| **A** | AI on code and data under the contract | Default setup below |
| **B** | AI on code, no customer data leaves their systems, or only through an approved cloud provider | Synthetic data only (policy skill `policy-client-data`); if the contract names a provider, route the model through Amazon Bedrock, Google Vertex AI or Microsoft Foundry for that project (`CLAUDE_CODE_USE_BEDROCK=1` and its settings in the project's `.claude/settings.json` env) |
| **C** | No AI | `data-class: C` in the `## AI-KIT` section: every skill stops; the hooks still run. Better: no Claude Code on that repo's machines or accounts |

The delivery lead records the class of each project in the project list and in the repo's `CLAUDE.md` (`$gdv-ai-kit:ship-init` asks). Unknown → B until confirmed.

## 2. Managed settings (non-negotiable for every engineer)

Start from `../templates/managed-settings.json`; review every line. Install on each machine (macOS `/Library/Application Support/ClaudeCode/managed-settings.json`, Linux `/etc/claude-code/managed-settings.json`) or push it as server-managed settings from the Claude admin console. Engineers cannot override managed keys.

- `permissions.deny`: secrets (`.env*`, keys, cloud and SSH credentials) and force pushes.
- `disableBypassPermissionsMode`: nobody runs with every check off.
- `enabledPlugins`: the GDV AI-KIT is on for everyone, so its hooks (`hooks/gates.py`) always run in AI-KIT repos.
- `allowedMcpServers`: only the connectors the company approved (step 4).

Team hooks that are not company-wide go into each repo's `.claude/settings.json` or `.claude/gdv-gates.json` (extra protected paths, deploy commands of that project).

## 3. Sandbox

`sandbox.enabled: true` runs every Bash command with OS-level filesystem and network isolation: writes stay inside the project, network goes through an allowlist. `autoAllowBashIfSandboxed` removes prompts for commands the sandbox already contains, so parallel sessions are not stuck on approvals. CI jobs that run Claude (`claude -p`) run in containers with short-lived scoped tokens and no production credentials.

## 4. Managed MCP

List the connectors each kind of project may use (tracker: Jira or Windshift; git provider; Sentry for Maintain). A connector that writes outside the company (email, chat, a customer's tracker) is allowed only where the contract allows it, and the hooks ask before any delete or ticket close.

## 5. Monitoring: usage telemetry is blocked

Claude Code can export usage metrics and events over OpenTelemetry. GlobalDev does not use it: the managed settings set `CLAUDE_CODE_ENABLE_TELEMETRY` to `0` and name no collector, and managed values win over project and user settings. The kit does not tag projects for it (`OTEL_RESOURCE_ATTRIBUTES` is no longer written; `$gdv-ai-kit:ship-doctor` check 11 reports a leftover tag or any telemetry that is on). Measurement of AI use comes only from the committed work log (`.ai/worklog/`, no names) and `scripts/metrics.py`, which are data the team already owns in git, for the pilot's before/after comparison.

## 6. Review gate on the developer's machine

The kit's review runs locally (`$gdv-ai-kit:ship-review`) when the work of a session is done, before commit, not in the git provider's CI, so it works for every customer's GitLab, GitHub or Bitbucket without setup there. The gate is the hook (`review-gate: block`), plus an optional git `pre-push` hook for pushes outside Claude. Limits, said plainly: a person can still push with `--no-verify` outside Claude; branch protection with a required approver on the provider remains the hard control. Where the customer allows it, the managed Code Review service or `claude-code-action` can run as a second layer.

## 7. Maintain loop (phase 2)

A scheduled job (GitLab schedule or cron) reads one metric per service (latency p95, error rate) as hourly readings, runs `scripts/control-band.py`, and on exit code 20 (3σ) runs `claude -p "$gdv-ai-kit:ship-maintain <breach.json>"` with the plugin, in a sandboxed runner with read-only access to code and monitoring. The output is a branch with a draft intent and a merge request for the on-call or PO to triage. Exit code 10 (2σ) only notifies a person. Never give this job deploy or rollback rights.

## 8. Rollout checklist

- [ ] Data class recorded for every active project
- [ ] Managed settings reviewed and installed; plugin enabled organisation-wide
- [ ] Sandbox on; CI runners for `claude -p` have no production credentials
- [ ] Approved MCP list published
- [ ] Managed settings set `CLAUDE_CODE_ENABLE_TELEMETRY` to `0` (telemetry blocked)
- [ ] `client-ai-statement.md` reviewed by the delivery lead and legal
- [ ] Baseline measured (`scripts/metrics.py` on the last 1–2 months) before the pilot starts
