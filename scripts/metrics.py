#!/usr/bin/env python3
"""Workflow metrics from git and the committed work log (GDV AI-KIT; replaces the 0.x retro skill).

  metrics.py [--since 2026-10-01] [--until 2026-11-01] [--repo PATH ...] [--intent-home PATH] [--branch main] [--md]

Per period, from data that is already in the repos (no tracker, no spreadsheet):
  - changes: commits on the main branch (--branch, default main or master) that name an ID: merge
    commits, and squash/rebase commits whose subject carries the ID
  - lead time: from the first commit that added <intent-home>/<ID>/intent.md to the merge of a branch
    named after ID (median and p85, hours)
  - first-pass review rate: share of changes whose first /ship-review verdict was "no-important"
    (from the ship-review work-log records: outcome done = no-important, gate = important)
  - rework rate: share of changes with a ship-build run that ended "done" more than once, or a ship-build
    run after a ship-review that found Important issues (outcome gate); a stop at the plan gate is not rework.
    /ship-build ends its run before it calls /ship-review, and a fix after an Important review starts a new run.
  - AI cost: tokens and active hours per skill and per role, from .ai/worklog/; tokens per model and
    effort level (by_model in records from 1.1.8; older records count under their models, effort "-")
Numbers are per change and per team, never per person. Measure a baseline before the pilot.
No third-party packages.
"""
import argparse, glob, json, os, re, statistics, subprocess, sys
from collections import defaultdict
from datetime import datetime, timezone


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def ts(s):
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))


def in_period(t, a):
    return (not a.since or t >= a.since) and (not a.until or t < a.until)


def worklog(repos):
    rs = []
    for repo in repos:
        for f in glob.glob(os.path.join(glob.escape(repo), ".ai", "worklog", "*", "*.json")):
            try:
                r = json.load(open(f, encoding="utf-8"))
                ts(r["ended"])
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                print(f"metrics: skipped unreadable record {f}", file=sys.stderr)
                continue
            if isinstance(r, dict) and r.get("id") and r.get("skill"):
                rs.append(r)
    return rs


def intent_created(home):
    """ID -> time of the first commit that added <home>/<ID>/intent.md."""
    out, repo = {}, home
    log = git(repo, "log", "--diff-filter=A", "--format=@%cI", "--name-only", "--", ".")
    t = None
    for line in log.splitlines():
        if line.startswith("@"):
            t = ts(line[1:])
        else:
            m = re.search(r"([^/]+)/intent\.md$", line)
            if m and t:
                out[m.group(1)] = min(t, out.get(m.group(1), t))
    return out


def main_branch(repo, name):
    if name:
        return name
    for b in ("main", "master", "origin/main", "origin/master"):
        if git(repo, "rev-parse", "--verify", "--quiet", b):
            return b
    return "HEAD"


def merges(repo, branch):
    """(time, ID) for each first-parent commit of the main branch that names an ID: merge commits, and the
    single commits of squash or rebase merges."""
    res, seen = [], set()
    for line in git(repo, "log", "--first-parent", main_branch(repo, branch), "--format=%cI\t%s").splitlines():
        t, _, subj = line.partition("\t")
        m = re.search(r"([A-Z][A-Z0-9]+-\d+|\d{8}-[a-z0-9-]+)", subj)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            res.append((ts(t), m.group(1)))
    return res


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))] if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since"); ap.add_argument("--until")
    ap.add_argument("--repo", action="append", default=[])
    ap.add_argument("--intent-home", default="intent")
    ap.add_argument("--branch", help="main branch to read merges from (default: main, else master)")
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args()
    a.since = ts(a.since + "T00:00:00+00:00") if a.since else None
    a.until = ts(a.until + "T00:00:00+00:00") if a.until else None
    repos = a.repo or ["."]
    created = intent_created(a.intent_home) if os.path.isdir(a.intent_home) else {}
    merged = [(t, i, r) for r in repos for t, i in merges(r, a.branch) if in_period(t, a)]
    lead = [(t - created[i]).total_seconds() / 3600 for t, i, _ in merged if i in created and t > created[i]]
    wl = [r for r in worklog(repos + ([a.intent_home] if os.path.isdir(a.intent_home) else []))
          if in_period(ts(r["ended"]), a)]
    first_review, built, rework, review_failed = {}, set(), set(), set()
    for r in sorted(wl, key=lambda r: r["ended"]):
        i, out = r["id"], r.get("outcome")
        if r["skill"] == "ship-review":
            first_review.setdefault(i, out)
            if out == "gate":
                review_failed.add(i)
        if r["skill"] == "ship-build" and out != "gate":   # a stop at the plan gate is not rework
            if i in built or i in review_failed:
                rework.add(i)
            if out == "done":
                built.add(i)
    builds = built | rework
    cost = defaultdict(lambda: [0, 0.0, 0])
    for r in wl:
        tok = r.get("tokens") if isinstance(r.get("tokens"), dict) else {}
        for k in (("skill", r["skill"]), ("role", r.get("role") or "-")):
            c = cost[k]; c[0] += 1; c[1] += float(r.get("active_s") or 0) / 3600
            c[2] += sum(v for v in tok.values() if isinstance(v, (int, float)))
        bm = [b for b in r.get("by_model") or [] if isinstance(b, dict)]
        if not bm and len(r.get("models") or []) == 1:   # before 1.1.8: one model, effort unknown
            bm = [{"model": r["models"][0], "effort": "-", "tokens": sum(v for v in tok.values() if isinstance(v, (int, float)))}]
        for b in bm:   # time is not split per model: tokens only
            c = cost[("model", f"{b.get('model', '-')} / {b.get('effort', '-')}")]
            c[0] += 1; c[1] = None
            c[2] += b.get("tokens") if isinstance(b.get("tokens"), (int, float)) else 0
    rows = [
        ("changes merged", len(merged)),
        ("lead time median h", round(statistics.median(lead), 1) if lead else "not measured"),
        ("lead time p85 h", round(pct(lead, 0.85), 1) if lead else "not measured"),
        ("first-pass review rate", f"{sum(1 for v in first_review.values() if v == 'done') / len(first_review):.0%}"
         if first_review else "not measured"),
        ("rework rate", f"{len(rework) / len(builds):.0%}" if builds else "not measured"),
    ]
    if a.md:
        print("| Measure | Value |\n|---|---|")
        for k, v in rows:
            print(f"| {k} | {v} |")
        print("\n| By | Name | Runs | Active h | Tokens |\n|---|---|---|---|---|")
        for (kind, name), (n, h, t) in sorted(cost.items()):
            print(f"| {kind} | {name} | {n} | {'-' if h is None else f'{h:.1f}'} | {t} |")
    else:
        for k, v in rows:
            print(f"{k}\t{v}")
        for (kind, name), (n, h, t) in sorted(cost.items()):
            print(f"{kind}:{name}\truns={n}\tactive_h={'-' if h is None else f'{h:.1f}'}\ttokens={t}")


if __name__ == "__main__":
    main()
