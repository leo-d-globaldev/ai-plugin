#!/usr/bin/env python3
"""Codex PreToolUse gate of the GDV AI-KIT (target: codex).

Wraps gates_core.py, a read-only copy of the Claude plugin's hooks/gates.py made by build.py, so the gate
logic has one source. What this wrapper adds for Codex:
  * Codex ignores "ask", so every "ask" becomes "deny" (fail closed). A "deny" of the core stays final.
  * File edits arrive as the tool "apply_patch" with the patch text in tool_input.command: the file paths
    are read from the patch and each one is checked as an Edit (protected paths, bug-fix test lock).
  * Approval token: after the person says yes in chat, repeat the command with GDV_APPROVED=GATE in front
    (GATE is the name in the deny message). A Bash command with the token passes its gate and is logged in
    .gdv/approvals.log; the token in any Bash command also records .gdv/approved/GATE, valid for 15 minutes,
    which is how an apply_patch gate is approved.
Output: a deny as JSON on stdout, or nothing. An internal error prints to stderr and lets the call through.
"""
import contextlib, hashlib, importlib, io, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
APPROVAL_SECONDS = 15 * 60
TOKEN_RE = re.compile(r"\bGDV_APPROVED=([A-Za-z][A-Za-z0-9-]*)")
PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$", re.M)


def load_core():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    return importlib.import_module("gates_core")


def run_core(core, data):
    """The decision the core prints for data, as (decision, gate, reason) or None."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        core.pre(data)
    last = None
    for line in buf.getvalue().splitlines():
        try:
            last = json.loads(line)["hookSpecificOutput"]
        except (ValueError, KeyError, TypeError):
            continue
    if not last:
        return None
    reason = last.get("permissionDecisionReason", "")
    reason = codex_names(reason)
    m = re.match(r"\[gate: ([^\]]+)\]", reason)
    return last.get("permissionDecision"), (m.group(1) if m else "unknown"), reason


def patch_paths(patch):
    seen, out = set(), []
    for p in PATCH_FILE_RE.findall(patch or ""):
        p = p.strip().strip('"')
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def repo_root(core, cwd):
    return core.git(cwd, "rev-parse", "--show-toplevel") or cwd


def log_approval(root, gate, command):
    try:
        os.makedirs(os.path.join(root, ".gdv"), exist_ok=True)
        with open(os.path.join(root, ".gdv", "approvals.log"), "a", encoding="utf-8") as f:
            f.write("%s\t%s\t%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), gate,
                                      hashlib.sha256(command.encode()).hexdigest()[:12]))
    except OSError as e:
        print(f"gates_codex: cannot write approval log: {e}", file=sys.stderr)


def record_tokens(root, command):
    """The token in a shell command records an approval for that gate (needed for apply_patch gates)."""
    gates = TOKEN_RE.findall(command)
    for g in gates:
        try:
            d = os.path.join(root, ".gdv", "approved")
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, g), "w").close()
        except OSError as e:
            print(f"gates_codex: cannot record approval: {e}", file=sys.stderr)
    return gates


def recently_approved(root, gate):
    try:
        return time.time() - os.path.getmtime(os.path.join(root, ".gdv", "approved", gate)) < APPROVAL_SECONDS
    except OSError:
        return False


def codex_names(text):
    """Claude slash command names in a gate reason become Codex skill names (a path such as skills/ship-review stays)."""
    return re.sub(r"(?<![\w/.-])/ship-review\b", "$gdv-ai-kit:ship-review", text)


def deny(gate, reason):
    reason = re.sub(r"\s*Ask the person to approve it or do it themselves; do not look for another way around\.$", "", reason)
    reason += (f" This needs a person: ask them in chat. Only after their yes, repeat it with GDV_APPROVED={gate} "
               f"(a shell command: put it in front; an edit: first run a shell command `GDV_APPROVED={gate} true`, "
               "valid for 15 minutes). Do not look for another way around.") if gate != "unknown" else ""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def decide(core, data):
    tool, tin = data.get("tool_name", ""), data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    root = repo_root(core, cwd)
    command = str(tin.get("command", ""))
    tokens = record_tokens(root, command) if tool == "Bash" else []
    if tool == "apply_patch":
        calls = [{"tool_name": "Edit", "tool_input": {"file_path": p}, "cwd": cwd} for p in patch_paths(command)]
    else:
        calls = [data]
    for call in calls:
        res = run_core(core, call)
        if not res:
            continue
        decision, gate, reason = res
        if decision == "deny":
            return deny_final(reason)
        if tool == "Bash" and gate in tokens:
            log_approval(root, gate, command)
            continue
        if tool != "Bash" and recently_approved(root, gate):  # apply_patch and mcp__ calls cannot carry the token
            log_approval(root, gate, command)
            continue
        return deny(gate, reason)


def deny_final(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0
    try:
        decide(load_core(), data)
    except Exception as e:  # noqa: BLE001
        print(f"gates_codex: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
