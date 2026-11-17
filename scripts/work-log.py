#!/usr/bin/env python3
"""Work log for one change: tokens and time, recorded in the repo for later analysis (GDV AI-KIT 1.0).

  work-log.py start <ID> --skill <name>     mark the start of work on ID (ticket key or intent ID) in this session
  work-log.py stop  <ID> [--outcome X]      close it and write the record (X: done, gate, blocked, failed;
                                            auto-closed is set by the SessionEnd hook)
  work-log.py show  <ID>                    running total for ID (all runs in this repo)
  work-log.py pending                       work logs still open
  work-log.py report [--md]                 totals per ID, per skill and per role from .ai/worklog/

Tokens come from the session transcript (message usage: input, output, cache write, cache read),
including the session's subagents. Time: wall clock between start and stop ("elapsed") and busy time
("active": gaps over 10 minutes between two messages are not counted).

Records: every stop writes one JSON file, .ai/worklog/YYYY-MM/<ended>-<ID>-<skill>.json, in the repo the
session runs in. One file per run, so parallel branches never conflict; commit them with the work.
Fields: id, skill, run, outcome, tokens, elapsed_s, active_s, models, efforts, by_model (tokens per model
and effort level, read from each assistant message), subagents, started, ended, session,
plugin, role (CLAUDE.local.md), repo. No names or emails, no secrets, never calls a tracker.
Local state (open logs, sessions) stays in .gdv/ (ignored by git).
"""
import glob, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

GAP = 600
FIELDS = ("input", "output", "cache_write", "cache_read")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(".gdv", "work")
RECORDS = os.path.join(".ai", "worklog")
# Claude names its transcript folder after the session folder, not the repo root; the hook passes it in GDV_SESSION_CWD
SESSION_CWD = os.environ.get("GDV_SESSION_CWD") or os.getcwd()


def repo_root(cwd):
    """The git top level of cwd (a session may run in a subfolder), else cwd."""
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd
    except Exception:  # noqa: BLE001
        return cwd


def utc(ts=None):
    return datetime.fromtimestamp(ts or time.time(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plugin_version():
    try:
        with open(os.path.join(HERE, "..", ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
            return json.load(fh).get("version", "?")
    except (OSError, ValueError):
        return "?"


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def session_info():
    """(session id, transcript, source); source is "env" when the id is known, "guess" otherwise.

    Order: 1) the id Claude Code puts in the environment (CLAUDE_CODE_SESSION_ID), 2) that session's
    file .gdv/sessions/ID.json written by the SessionStart hook, 3) .gdv/session.json = the last
    session that started in this folder (a guess when several sessions share the folder: warns),
    4) GDV_TRANSCRIPT, 5) the newest transcript of the folder.
    Only 1-2 are sure. 3-5 are guesses: any session started later in the folder (a side session, a
    review session) rewrites .gdv/session.json, so a start recorded from it can name another session
    (seen 2026-11-13 with plugin 0.36.0, which had only 3: the open start then carried the side session's id, the side
    session's SessionEnd hook auto-closed it and the stop measured that session with 0 tokens).
    """
    cfg = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude"))
    enc = re.sub(r"[^A-Za-z0-9]", "-", SESSION_CWD)
    d = os.path.join(cfg, "projects", enc)
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        p = os.path.join(d, sid + ".jsonl")
        if not os.path.isfile(p):
            hits = glob.glob(os.path.join(glob.escape(cfg), "projects", "*", sid + ".jsonl"))
            p = hits[0] if hits else ""
        if not p:
            tp = _read_json(os.path.join(".gdv", "sessions", sid + ".json")).get("transcript_path", "")
            p = tp if tp and os.path.isfile(tp) else ""
        if p:
            return sid, p, "env"
    s = _read_json(os.path.join(".gdv", "session.json"))
    if s.get("transcript_path") and os.path.isfile(s["transcript_path"]):
        recent = [f for f in glob.glob(os.path.join(".gdv", "sessions", "*.json"))
                  if time.time() - os.path.getmtime(f) < 86400]
        if len(recent) > 1:
            print("work-log: several sessions started in this folder and the calling session is unknown "
                  "(no CLAUDE_CODE_SESSION_ID); measuring the last one that started, which may be wrong",
                  file=sys.stderr)
        return s.get("session_id", ""), s["transcript_path"], "guess"
    p = os.environ.get("GDV_TRANSCRIPT")
    if p and os.path.isfile(p):
        return os.path.basename(p)[:-6], p, "guess"
    files = glob.glob(os.path.join(glob.escape(d), "*.jsonl"))
    if not files:
        return "", None, "guess"
    p = max(files, key=os.path.getmtime)
    return os.path.basename(p)[:-6], p, "guess"


def parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def measure(transcript, t0):
    base = transcript[:-len(".jsonl")]
    subs = sorted(glob.glob(os.path.join(glob.escape(base), "subagents", "*.jsonl")))
    tot, seen, stamps, models, used_subs = dict.fromkeys(FIELDS, 0), {}, [], set(), set()
    for f in [transcript] + subs:
        try:
            fh = open(f, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(d, dict):
                    continue
                ts = parse_ts(d.get("timestamp", ""))
                if ts is None or ts < t0:
                    continue
                stamps.append(ts)
                if d.get("type") != "assistant":
                    continue
                m = d.get("message") or {}
                model = m.get("model") if m.get("model") and not str(m["model"]).startswith("<") else None
                seen[(f, m.get("id") or d.get("uuid"))] = (m.get("usage") or {}, model or "-",
                                                          str(d.get("effort") or os.environ.get("CLAUDE_EFFORT") or "-"))
                if model:
                    models.add(model)
                if f != transcript:
                    used_subs.add(f)
    per = {}
    for u, model, effort in seen.values():
        n = {"input": int(u.get("input_tokens") or 0), "output": int(u.get("output_tokens") or 0),
             "cache_write": int(u.get("cache_creation_input_tokens") or 0),
             "cache_read": int(u.get("cache_read_input_tokens") or 0)}
        for k, v in n.items():
            tot[k] += v
        per[(model, effort)] = per.get((model, effort), 0) + sum(n.values())
    stamps.sort()
    active = sum(b - a for a, b in zip(stamps, stamps[1:]) if b - a <= GAP)
    by_model = [{"model": m, "effort": e, "tokens": t} for (m, e), t in sorted(per.items()) if t]
    return tot, active, sorted(models), len(used_subs), by_model


def key_ok(key):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", key) or ".." in key:
        sys.exit(f"work-log: '{key}' is not a ticket key or intent ID (PROJ-123, 20261115-checkout-retry)")
    return key


def state_path(key):
    return os.path.join(WORK, key_ok(key) + ".json")


def load(key):
    try:
        with open(state_path(key), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"key": key, "runs": 0}


def save(key, st):
    os.makedirs(WORK, exist_ok=True)
    with open(state_path(key), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2)


def records():
    rs = []
    for f in sorted(glob.glob(os.path.join(RECORDS, "*", "*.json"))):
        r = _read_json(f)
        if r.get("id"):
            rs.append(r)
    return rs


def role():
    try:
        text = open("CLAUDE.local.md", encoding="utf-8").read()
    except OSError:
        return ""
    m = re.search(r"^## AI-KIT me\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    r = re.search(r"^-\s*role:\s*(\S[^\n]*)$", m.group(1), re.M) if m else None
    return r.group(1).strip() if r else ""


def _num(n):
    """1234567 -> 1.234.567 (readable line only; the JSON block keeps plain numbers)."""
    return f"{int(n):,}".replace(",", ".")


def _dur(sec):
    sec = int(sec)
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m {sec % 60:02d}s"
    return f"{sec // 3600}h {sec % 3600 // 60:02d}m"


def summary(r):
    return (f"work-log: {r['id']} · {r['skill']} · run {r['run']} · {r['outcome']} · "
            f"active {_dur(r['active_s'])} · tokens {_num(sum(r['tokens'].values()))} → {r['_file']}")


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def stop(key, outcome="done", by="skill"):
    st = load(key)
    o = st.get("open")
    if not o:
        return None
    if by == "skill" and o.get("sid_from") != "env":
        # the start guessed its session (older plugin, or no CLAUDE_CODE_SESSION_ID); when this stop
        # knows its own session for sure, measure that one: the start may name a side session
        sid, tr, src = session_info()
        if src == "env" and sid != o.get("session"):
            print(f"work-log: the start of {key} recorded session {str(o.get('session'))[:8]} (a guess); "
                  f"measuring this session {sid[:8]} instead", file=sys.stderr)
            o.update(session=sid, transcript=tr, sid_from="env")
    if o.get("transcript") and os.path.isfile(o["transcript"]):
        tokens, active, models, subs, by_model = measure(o["transcript"], o["t0"])
        measured = True
    else:
        tokens, active, models, subs, measured = dict.fromkeys(FIELDS, 0), 0, [], 0, False
        by_model = []
    st["runs"] = st.get("runs", 0) + 1
    r = {"id": key, "skill": o.get("skill", "unknown"), "outcome": outcome, "run": st["runs"],
         "tokens": tokens, "elapsed_s": int(time.time() - o["t0"]), "active_s": int(active),
         "models": models, "efforts": sorted({b["effort"] for b in by_model if b["effort"] != "-"}),
         "by_model": by_model, "subagents": subs, "started": o["started"], "ended": utc(),
         "session": o.get("session", ""), "plugin": plugin_version(), "measured": measured,
         "closed_by": by, "role": role(), "repo": os.path.basename(os.getcwd())}
    del st["open"]
    save(key, st)
    d = os.path.join(RECORDS, r["ended"][:7])
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{r['ended'].replace(':', '').replace('-', '')}-{key}-{r['skill']}.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
        fh.write("\n")
    r["_file"] = f
    return r


def num(v):
    return v if isinstance(v, (int, float)) else 0


def tokens(r):
    t = r.get("tokens")
    return sum(num(v) for v in t.values()) if isinstance(t, dict) else 0


def main(a):
    os.chdir(repo_root(os.getcwd()))   # records and .gdv/ live at the repo root, whatever the session folder
    if len(a) < 2 or a[1] not in ("start", "stop", "show", "pending", "report"):
        sys.exit(__doc__)
    cmd = a[1]
    if cmd == "pending":
        opens = []
        for f in sorted(glob.glob(os.path.join(WORK, "*.json"))):
            try:
                st = json.load(open(f, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if st.get("open"):
                opens.append(f"open: {st['key']} ({st['open'].get('skill')}, since {st['open']['started']})")
        print("\n".join(opens) or "work-log: nothing open")
        return
    if cmd == "report":
        agg = {}
        for r in records():
            for k in (("id", r["id"]), ("skill", r["skill"]), ("role", r.get("role") or "-")):
                g = agg.setdefault(k, {"runs": 0, "tokens": 0, "active_s": 0, "elapsed_s": 0})
                g["runs"] += 1
                g["tokens"] += tokens(r)
                g["active_s"] += num(r.get("active_s"))
                g["elapsed_s"] += num(r.get("elapsed_s"))
            for b in r.get("by_model") or []:   # tokens only: time is not split per model
                if isinstance(b, dict):
                    g = agg.setdefault(("model", f"{b.get('model', '-')} / {b.get('effort', '-')}"),
                                       {"runs": 0, "tokens": 0, "active_s": 0, "elapsed_s": 0})
                    g["runs"] += 1
                    g["tokens"] += num(b.get("tokens"))
        md = "--md" in a
        if md:
            print("| by | name | runs | tokens | active h | elapsed h |\n|---|---|---|---|---|---|")
        for (kind, name), g in sorted(agg.items()):
            row = [kind, name, g["runs"], g["tokens"], round(g["active_s"] / 3600, 2), round(g["elapsed_s"] / 3600, 2)]
            print("| " + " | ".join(map(str, row)) + " |" if md else "\t".join(map(str, row)))
        return
    if len(a) < 3:
        sys.exit(__doc__)
    key = key_ok(a[2])
    if cmd == "show":
        rs = [r for r in records() if r["id"] == key]
        tok = sum(tokens(r) for r in rs)
        print(f"work-log total {key}: runs={len(rs)} tokens={tok} "
              f"active_s={sum(num(r.get('active_s')) for r in rs)} elapsed_s={sum(num(r.get('elapsed_s')) for r in rs)}")
        return
    if cmd == "start":
        skill = opt(a, "--skill", "unknown")
        st = load(key)
        if st.get("open"):
            print(f"work-log: {key} already open since {st['open']['started']} ({st['open'].get('skill')}); keeping it")
            return
        sid, tr, src = session_info()
        if src != "env":
            print(f"work-log: the calling session is not known for sure (no CLAUDE_CODE_SESSION_ID); recorded "
                  f"{sid[:8] or 'none'} as a guess: the SessionEnd hook will not auto-close it, and stop "
                  f"re-measures its own session when it knows it", file=sys.stderr)
        # CPA-130: a second open log in one session would count the same tokens and time on both items
        for f in glob.glob(os.path.join(WORK, "*.json")):
            o = _read_json(f).get("open")
            other = os.path.basename(f)[:-len(".json")]
            if src == "env" and o and o.get("session") == sid and other != key:
                sys.exit(f"work-log: this session already has {other} open; run `work-log.py stop {other}` "
                         f"first, so the same tokens and time are not counted on {key} too")
        if not tr:
            print("work-log: no session transcript found; tokens cannot be measured, time still is", file=sys.stderr)
        st["open"] = {"skill": skill, "t0": time.time(), "started": utc(), "session": sid, "transcript": tr,
                      "sid_from": src}
        save(key, st)
        print(f"work-log: started {key} ({skill}) at {st['open']['started']}")
        return
    outcome = opt(a, "--outcome", "done")
    if outcome not in ("done", "gate", "blocked", "failed", "auto-closed"):
        sys.exit("work-log: --outcome is one of done, gate, blocked, failed")
    r = stop(key, outcome, "hook" if outcome == "auto-closed" else "skill")
    if not r:
        print(f"work-log: {key} has no open start; nothing measured", file=sys.stderr)
        sys.exit(1)
    text = summary(r)
    if not r["measured"]:
        text += " (tokens not measured: no session transcript)"
    print(text)


if __name__ == "__main__":
    main(sys.argv)
