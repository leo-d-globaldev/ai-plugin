#!/usr/bin/env python3
"""Effective model and effort settings of the GDV AI-KIT (CONVENTIONS section 1). Read-only; never fails a run.

  kit-config.py models [--rating easy|medium|hard] [--host claude|codex] [--dir DIR] [--json]

Keys: model-easy, model-medium, model-hard (the session that builds), model-verify, model-review. Value MODEL/EFFORT;
either part may be left out (sonnet, /high); empty or "default" = inherit (the session's own). Per key: the personal
file (## AI-KIT me of CLAUDE.local.md, then AGENTS.local.md), then the team file (## AI-KIT of CLAUDE.md, then
AGENTS.md), then unset. A value with a bad shape is reported as a problem and skipped (the next level is used).
Exit code is always 0. --rating adds the line for that rating under the name "build"."""
import argparse, json, os, re, sys

KEYS = ("model-easy", "model-medium", "model-hard", "model-verify", "model-review")
EFFORTS = {"claude": ("low", "medium", "high", "xhigh", "max"),
           # codex: names of ReasoningEffort in openai/codex (read from the source, not run); the model decides which it accepts
           "codex": ("none", "minimal", "low", "medium", "high", "xhigh", "max")}
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


def section(path, head):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"^## " + re.escape(head) + r"[ \t]*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def raw(body, key):
    m = re.search(r"^-[ \t]*" + re.escape(key) + r":[ \t]*([^\n#]*)", body or "", re.M)
    return m.group(1).strip() if m else None


def parse(value, host):
    """-> (model, effort, problem). Empty or default: (None, None, None)."""
    if value is None or value == "" or value.lower() == "default":
        return None, None, None
    model, _, effort = value.partition("/")
    model, effort = model.strip(), effort.strip()
    if model.lower() in ("", "default", "inherit"):
        model = ""
    if model and not MODEL_RE.match(model):
        return None, None, "model '%s' has an odd shape (letters, digits, . _ : - only)" % model
    if effort and effort not in EFFORTS[host]:
        return None, None, "effort '%s' is not one of %s" % (effort, "|".join(EFFORTS[host]))
    return model or None, effort or None, None


def levels(root):
    local, team = [], []
    for name in ("CLAUDE.local.md", "AGENTS.local.md"):
        b = section(os.path.join(root, name), "AI-KIT me")
        if b is not None:
            local.append((name, b))
    for name in ("CLAUDE.md", "AGENTS.md"):
        b = section(os.path.join(root, name), "AI-KIT")
        if b is not None:
            team.append((name, b))
    return local + team


def resolve(root, host):
    out, problems = {}, []
    lv = levels(root)
    for key in KEYS:
        out[key] = {"model": None, "effort": None, "source": "unset"}
        for src, body in lv:
            v = raw(body, key)
            if v is None:
                continue
            model, effort, bad = parse(v, host)
            if bad:
                problems.append("%s in %s: %s" % (key, src, bad))
                continue
            out[key] = {"model": model, "effort": effort, "source": src}
            break
    return out, problems


def fmt(e):
    if e["source"] == "unset" or not (e["model"] or e["effort"]):
        return "inherit" if e["source"] != "unset" else "unset"
    return "%s/%s" % (e["model"] or "", e["effort"] or "") if e["effort"] else e["model"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["models"])
    ap.add_argument("--rating", choices=["easy", "medium", "hard"])
    ap.add_argument("--host", choices=["claude", "codex"], default=None, help="default: codex when worklog_codex.py is next to this file (the Codex package), else claude")
    ap.add_argument("--dir", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.host:
        a.host = "codex" if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "worklog_codex.py")) else "claude"
    try:
        res, problems = resolve(os.path.abspath(a.dir), a.host)
    except Exception as e:  # noqa: BLE001  never break a run
        res, problems = {k: {"model": None, "effort": None, "source": "unset"} for k in KEYS}, ["could not read config: %s" % e]
    if a.rating:
        res["build"] = res["model-" + a.rating]
    if a.json:
        print(json.dumps({"values": res, "problems": problems}, indent=1))
        return 0
    for k, e in res.items():
        src = "" if e["source"] == "unset" else " (from %s)" % e["source"]
        print("%s: %s%s" % (k, fmt(e), src))
    for p in problems:
        print("problem: " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
