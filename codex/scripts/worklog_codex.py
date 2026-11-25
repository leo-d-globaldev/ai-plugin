#!/usr/bin/env python3
"""Work log for Codex (GDV AI-KIT, Codex target). Same records as the Claude scripts/work-log.py, written by this file
alone: it imports nothing from the Claude plugin and the Claude plugin does not know it.

CLI (skills call it):
  worklog_codex.py start <ID> --skill NAME     mark the start of work on ID in this session
  worklog_codex.py stop  <ID> [--outcome X]    close it and write .ai/worklog/YYYY-MM/<ended>-<ID>-<skill>.json
  worklog_codex.py show <ID> | pending
Hooks (hooks.json calls them, JSON on stdin):
  worklog_codex.py session-start | session-end

Tokens: from the Codex session file (hook input transcript_path): the last cumulative total_token_usage minus the
value at start. tokens is null when the file cannot be read or has no such event. Model: turn_context or the hook's
model field. Effort: the `effort` of turn_context items when present (efforts stays empty otherwise). Role: AGENTS.local.md, else CLAUDE.local.md. Level: "- worklog: off|remind|strict" in the CLAUDE.md
AI-KIT section (strict runs as remind: Codex edits arrive as apply_patch). Never blocks on an internal error.
Local state is in .gdv/ (ignored), records in .ai/worklog/ (committed). Codex SessionEnd allows 1 to 3 s: no subprocess."""
import glob, json, os, re, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ("input", "output", "cache_write", "cache_read")
GAP = 600


def utc(ts=None):
    return datetime.fromtimestamp(ts or time.time(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def repo_root(cwd):
    d = os.path.abspath(cwd)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        p = os.path.dirname(d)
        if p == d:
            return os.path.abspath(cwd)
        d = p


def level(root):
    env = os.environ.get("GDV_WORKLOG", "").strip().lower()
    text = ""
    for name in ("AGENTS.md", "CLAUDE.md"):
        try:
            text = open(os.path.join(root, name), encoding="utf-8").read()
        except OSError:
            continue
        if re.search(r"^## AI-KIT\s*$", text, re.M):
            break
    m = re.search(r"^## AI-KIT\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return "off"
    if env in ("off", "remind", "strict"):
        return env
    lm = re.search(r"^-\s*worklog:\s*(off|remind|strict)\b", m.group(1), re.M | re.I)
    return lm.group(1).lower() if lm else "remind"


def role(root):
    for name in ("AGENTS.local.md", "CLAUDE.local.md"):
        try:
            text = open(os.path.join(root, name), encoding="utf-8").read()
        except OSError:
            continue
        m = re.search(r"^## AI-KIT me\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
        r = re.search(r"^-[ \t]*role:[ \t]*(\S[^\n]*)$", m.group(1), re.M) if m else None
        if r:
            return r.group(1).strip()
    return ""


def version():
    return open(os.path.join(HERE, "..", "VERSION")).read().strip() if os.path.isfile(os.path.join(HERE, "..", "VERSION")) \
        else read_json(os.path.join(HERE, "..", ".claude-plugin", "plugin.json")).get("version", "?")


def measure(path):
    """(tokens dict or None, models, efforts) from a Codex session file; tolerant of unknown lines. efforts: the `effort`
    of turn_context items (field of TurnContextItem in openai/codex; read from its source, not seen in a real file here)."""
    if not path or not os.path.isfile(path):
        return None, [], []
    last, models, efforts = None, [], []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "total_token_usage" not in line and '"model"' not in line and '"effort"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                p = o.get("payload") if isinstance(o, dict) else None
                u = ((p or {}).get("info") or {}).get("total_token_usage") if isinstance(p, dict) else None
                if isinstance(u, dict):
                    last = u
                m = (p or {}).get("model") if isinstance(p, dict) else None
                if isinstance(m, str) and m not in models:
                    models.append(m)
                e = (p or {}).get("effort") if isinstance(p, dict) and o.get("type") == "turn_context" else None
                if isinstance(e, str) and re.fullmatch(r"[a-z]{3,12}", e) and e not in efforts:
                    efforts.append(e)
    except OSError:
        return None, [], []
    if not last:
        return None, models, efforts
    cached = int(last.get("cached_input_tokens") or 0)
    return {"input": max(int(last.get("input_tokens") or 0) - cached, 0), "output": int(last.get("output_tokens") or 0),
            "cache_write": 0, "cache_read": cached}, models, efforts


def sub(a, b):
    if a is None:
        return None
    return {k: max(a[k] - (b or {}).get(k, 0), 0) for k in FIELDS}


def state_path(root, key):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", key) or ".." in key:
        sys.exit("worklog: '%s' is not a ticket key or intent ID (PROJ-123, 20261115-checkout-retry)" % key)
    return os.path.join(root, ".gdv", "work", key + ".json")


def load(root, key):
    return read_json(state_path(root, key)) or {"key": key, "runs": 0}


def save(root, key, st):
    p = state_path(root, key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2)


def session(root):
    """(session id, transcript, model, source): 'env' when the id is known for sure, else 'guess' (the last session)."""
    for var in ("GDV_SESSION_ID", "CODEX_THREAD_ID", "CODEX_SESSION_ID"):
        sid = os.environ.get(var, "").strip()
        if re.fullmatch(r"[A-Za-z0-9_-]+", sid):
            s = read_json(os.path.join(root, ".gdv", "sessions", sid + ".json"))
            if s:
                return sid, s.get("transcript_path", ""), s.get("model", ""), "env"
    s = read_json(os.path.join(root, ".gdv", "session.json"))
    return s.get("session_id", ""), s.get("transcript_path", ""), s.get("model", ""), "guess"


def open_logs(root, sid=None):
    out = []
    for f in glob.glob(os.path.join(glob.escape(root), ".gdv", "work", "*.json")):
        st = read_json(f)
        o = st.get("open")
        if o and (sid is None or o.get("session") == sid):
            out.append((st["key"], o))
    return out


def start(root, key, skill):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,40}", skill or ""):
        sys.exit("worklog: '%s' is not a skill name" % skill)
    st = load(root, key)
    if st.get("open"):
        print("worklog: %s already open since %s (%s); keeping it. Not this work? Close it with: "
              "python3 scripts/worklog_codex.py stop %s --outcome failed" % (key, st["open"]["started"], st["open"].get("skill"), key))
        return
    sid, tr, model, src = session(root)
    if src == "env":
        others = [k for k, _ in open_logs(root, sid) if k != key]
        if others:
            print("worklog: this session already has open work log(s) %s; close them (stop KEY --outcome done|gate|blocked|failed) "
                  "so tokens are not counted twice" % ", ".join(others), file=sys.stderr)
    tok, _, _ = measure(tr)
    st["open"] = {"skill": skill, "t0": time.time(), "started": utc(), "session": sid, "transcript": tr,
                  "sid_from": src, "base": tok, "model": model}
    save(root, key, st)
    print("worklog: started %s (%s)%s" % (key, skill, "" if src == "env" else " - session guessed (hooks not trusted?)"))


def stop(root, key, outcome="done", by="skill"):
    st = load(root, key)
    o = st.get("open")
    if not o:
        print("worklog: no open work log for %s" % key)
        return None
    if by == "skill" and o.get("sid_from") != "env":
        # the start guessed its session (it may name a side session, e.g. a codex exec child);
        # when this stop knows its own session for sure, measure that one from zero
        sid, tr, model, src = session(root)
        if src == "env" and sid != o.get("session"):
            print("worklog: the start of %s recorded session %s (a guess); measuring this session %s instead "
                  "(tokens count from the session start and may include earlier work)"
                  % (key, str(o.get("session"))[:8], sid[:8]), file=sys.stderr)
            o.update(session=sid, transcript=tr, model=model, sid_from="env", base=None, rebased=True)
    tok, models, efforts = measure(o.get("transcript"))
    tokens = sub(tok, o.get("base"))
    if not models and o.get("model"):
        models = [o["model"]]
    st["runs"] = st.get("runs", 0) + 1
    elapsed = int(time.time() - o["t0"])
    r = {"id": key, "skill": o.get("skill", "unknown"), "outcome": outcome, "run": st["runs"], "tokens": tokens,
         "tokens_total": sum(tokens.values()) if tokens else None, "elapsed_s": elapsed, "active_s": elapsed,
         "models": models, "efforts": efforts, "by_model": [], "subagents": 0, "started": o["started"], "ended": utc(),
         "session": o.get("session", ""), "plugin": "codex-" + version(), "measured": tokens is not None,
         "closed_by": by, "role": role(root), "repo": os.path.basename(root),
         "tokens_basis": "whole-session" if (o.get("rebased") or o.get("base") is None) else "since-start"}
    del st["open"]
    save(root, key, st)
    d = os.path.join(root, ".ai", "worklog", r["ended"][:7])
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, "%s-%s-%s.json" % (r["ended"].replace(":", "").replace("-", ""), key, r["skill"]))
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
        fh.write("\n")
    print("worklog: %s %s closed (%s), tokens %s -> %s" % (key, r["skill"], outcome, r["tokens_total"], os.path.relpath(f, root)))
    return r


def hook(mode):
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    root = repo_root(data.get("cwd") or os.getcwd())
    lvl = level(root)
    if lvl == "off":
        return
    sid = data.get("session_id", "")
    if mode == "session-start":
        rec = {"session_id": sid, "transcript_path": data.get("transcript_path", ""), "model": data.get("model", "")}
        os.makedirs(os.path.join(root, ".gdv"), exist_ok=True)
        with open(os.path.join(root, ".gdv", "session.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        if re.fullmatch(r"[A-Za-z0-9_-]+", sid or ""):
            sd = os.path.join(root, ".gdv", "sessions")
            os.makedirs(sd, exist_ok=True)
            with open(os.path.join(sd, sid + ".json"), "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
            for old in glob.glob(os.path.join(glob.escape(sd), "*.json")):
                if time.time() - os.path.getmtime(old) > 7 * 86400:
                    os.remove(old)
        note = ("AI-KIT work log (%s): each skill run on an intent starts with python3 <plugin>/scripts/worklog_codex.py "
                "start <ID> --skill <name> and ends with stop; the record goes to .ai/worklog/ and is committed with the work."
                % ("remind" if lvl == "strict" else lvl))
        opens = ["open: %s (%s, since %s)" % (k, o.get("skill"), o.get("started")) for k, o in open_logs(root)]
        if opens:
            note += "\nWork logs still open (stop them when their work is done):\n" + "\n".join(opens)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": note}}))
    elif mode == "session-end":
        for key, o in open_logs(root, sid):
            if o.get("sid_from") == "env":
                stop(root, key, "auto-closed", by="hook")


def main(a):
    if len(a) < 2 or a[1] not in ("start", "stop", "show", "pending", "session-start", "session-end"):
        sys.exit(__doc__)
    if a[1] in ("session-start", "session-end"):
        try:
            hook(a[1])
        except Exception as e:  # noqa: BLE001
            print("worklog hook: %s" % e, file=sys.stderr)
        return
    root = repo_root(os.getcwd())
    cmd = a[1]
    if cmd == "pending":
        opens = ["open: %s (%s, since %s)" % (k, o.get("skill"), o.get("started")) for k, o in open_logs(root)]
        print("\n".join(opens) or "worklog: nothing open")
        return
    if len(a) < 3:
        sys.exit("worklog: %s needs an ID" % cmd)
    key = a[2]
    def opt(name, default):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default
    if cmd == "start":
        start(root, key, opt("--skill", "unknown"))
    elif cmd == "stop":
        stop(root, key, opt("--outcome", "done"))
    else:
        tot, n = 0, 0
        for f in glob.glob(os.path.join(glob.escape(root), ".ai", "worklog", "*", "*-%s-*.json" % key)):
            r = read_json(f)
            n += 1
            tot += r.get("tokens_total") or 0
        print("worklog: %s: %d runs, %d tokens" % (key, n, tot))


if __name__ == "__main__":
    main(sys.argv)
