#!/usr/bin/env python3
"""Work-log hook (GDV AI-KIT: every job has an intent ID or ticket, and its cost is recorded in the repo).

Active only in a repo whose CLAUDE.md has a "## AI-KIT" section. Level from the line
"- worklog: off|remind|strict" in that section, or the env var GDV_WORKLOG (wins); default remind.

  session-start  saves session id + transcript path in .gdv/sessions/ID.json (one file per session)
                 and in .gdv/session.json (the last session of the folder, fallback only);
                 scripts/work-log.py reads them; tells Claude about work logs still open.
  pre            before Edit/Write/MultiEdit/NotebookEdit: no open work log in this session ->
                 remind: let it through with a note to Claude; strict: deny, with the fix.
                 Writes under .gdv/ and .ai/ are always allowed.
  session-end    closes the work logs this session left open (outcome auto-closed, closed_by=hook) so the time and tokens are not lost; the next session-start says
                 they are still recorded. Only starts that knew their session (sid_from=env): a start that
                 guessed it may carry another session's id, and closing it would end the caller's log.

Never blocks on an internal error. No third-party packages.
"""
import glob, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WL = os.path.join(HERE, "..", "scripts", "work-log.py")


def repo_root(cwd):
    """The git top level of cwd (a session may run in a subfolder), else cwd."""
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd
    except Exception:  # noqa: BLE001
        return cwd


def level(cwd):
    env = os.environ.get("GDV_WORKLOG", "").strip().lower()
    try:
        text = open(os.path.join(cwd, "CLAUDE.md"), encoding="utf-8").read()
    except OSError:
        text = ""
    m = re.search(r"^## AI-KIT\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return "off"
    if env in ("off", "remind", "strict"):
        return env
    lm = re.search(r"^-\s*worklog:\s*(off|remind|strict)\b", m.group(1), re.M | re.I)
    return lm.group(1).lower() if lm else "remind"


def open_logs(cwd, session=None):
    out = []
    for f in glob.glob(os.path.join(glob.escape(cwd), ".gdv", "work", "*.json")):
        try:
            st = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        o = st.get("open")
        if o and (session is None or o.get("session") == session):
            out.append((st["key"], o))
    return out


def emit(obj):
    print(json.dumps(obj))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    session_cwd = data.get("cwd") or os.getcwd()
    os.environ["GDV_SESSION_CWD"] = session_cwd   # read by work-log.py (transcript folder)
    cwd = repo_root(session_cwd)
    lvl = level(cwd)
    if lvl == "off":
        return
    sid = data.get("session_id", "")
    if mode == "session-start":
        os.makedirs(os.path.join(cwd, ".gdv"), exist_ok=True)
        rec = {"session_id": sid, "transcript_path": data.get("transcript_path", "")}
        with open(os.path.join(cwd, ".gdv", "session.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh)  # last session of the folder: fallback only (CPA-128)
        if re.fullmatch(r"[A-Za-z0-9_-]+", sid):
            sd = os.path.join(cwd, ".gdv", "sessions")
            os.makedirs(sd, exist_ok=True)
            with open(os.path.join(sd, sid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
            for old in glob.glob(os.path.join(glob.escape(sd), "*.json")):
                if time.time() - os.path.getmtime(old) > 7 * 86400:
                    os.remove(old)
        try:
            pend = subprocess.run([sys.executable, WL, "pending"], cwd=cwd, capture_output=True, text=True,
                                  timeout=20).stdout.strip()
        except subprocess.SubprocessError:
            pend = ""
        note = (f"AI-KIT work log ({lvl}): each skill run on an intent starts with "
                f"python3 \"${{CLAUDE_PLUGIN_ROOT}}/scripts/work-log.py\" start <ID> --skill <name> and ends with stop; "
                f"the record goes to .ai/worklog/ and is committed with the work.")
        if pend and not pend.startswith("work-log: nothing"):
            note += "\nWork logs still open (stop them when their work is done):\n" + pend
        emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}})
        return
    if mode == "session-end":
        for key, o in open_logs(cwd, sid):
            if o.get("sid_from") != "env":
                continue  # the start only guessed its session: it may be another session's work (stop re-measures it)
            try:
                subprocess.run([sys.executable, WL, "stop", key, "--outcome", "auto-closed"], cwd=cwd,
                               capture_output=True, timeout=60)
            except subprocess.SubprocessError:
                print(f"work-log: could not auto-close {key} in time", file=sys.stderr)
        return
    if mode != "pre":
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    path = str(ti.get("file_path") or ti.get("notebook_path") or "")
    if re.search(r"(^|[\\/])\.(gdv|ai)[\\/]", path):
        return
    if open_logs(cwd, sid):
        return
    msg = ("[work log] No open work log in this session. Run "
           "`python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/work-log.py\" start <ID> --skill <name>` first; ID is the "
           "ticket key or the intent ID (no intent yet: ask the person which ticket, or use YYYYMMDD-slug).")
    if lvl == "strict":
        emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                     "permissionDecisionReason": msg}})
    else:
        emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}})


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"work-log hook: {e}", file=sys.stderr)
