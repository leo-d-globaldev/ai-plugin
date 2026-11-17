#!/usr/bin/env python3
"""SessionStart hook: tells Claude, in a few lines, how this repo uses the GDV AI-KIT, so the right
skill loads from plain words ("làm tiếp", "fix bug này") without the person naming it.

Active only when CLAUDE.md has a "## AI-KIT" section. Prints: the config, the person's role from
CLAUDE.local.md, and the open intents (ID, status, title) of the intent home. Never blocks.
"""
import glob, json, os, re, subprocess, sys

ORDER = ["draft", "approved", "specified", "planned", "building", "review", "merged", "testing"]


def repo_root(cwd):
    """The git top level of cwd (a session may run in a subfolder), else cwd."""
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else cwd
    except Exception:  # noqa: BLE001
        return cwd


def section(path, name):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return dict(re.findall(r"^-\s*([a-z-]+):\s*(\S[^#\n]*?)\s*(?:#.*)?$", m.group(1), re.M)) if m else None


def front(path):
    try:
        text = open(path, encoding="utf-8").read(4000)
    except OSError:
        return {}
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    return dict(re.findall(r"^([a-z]+):\s*\"?(.*?)\"?\s*$", m.group(1), re.M)) if m else {}


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    cwd = repo_root(data.get("cwd") or os.getcwd())
    kit = section(os.path.join(cwd, "CLAUDE.md"), "AI-KIT")
    if kit is None:
        return
    me = section(os.path.join(cwd, "CLAUDE.local.md"), "AI-KIT me") or {}
    home = os.path.normpath(os.path.join(cwd, kit.get("intent-home", "./intent")))
    lines = [f"GDV AI-KIT repo. mode={kit.get('mode', 'manual')} data-class={kit.get('data-class', 'B?')} "
             f"adapter={kit.get('adapter', 'none')} intent-home={kit.get('intent-home', './intent')} "
             f"role={me.get('role', 'not set (run /ship-init)')}."]
    if kit.get("data-class", "").strip().upper() == "C":
        lines.append("Data class C: the customer forbids AI on this project. Do not read or change the code.")
    else:
        lines.append("Pick the skill from the person's words: idea → ship-intent, spec/design → ship-spec, "
                     "ticket/implement/fix → ship-build, review/push/PR → ship-review, test/QC/bug → ship-test; "
                     "unsure → /ship. Gates (push without review, main branch, production, protected paths) are hooks.")
        if not os.path.isdir(home):
            lines.append(f"Intent home {home} not found (a docs repo not cloned?).")
        else:
            open_ = []
            for f in sorted(glob.glob(os.path.join(glob.escape(home), "*", "intent.md"))):
                fm = front(f)
                st = fm.get("status", "draft")
                if st in ORDER:
                    par = fm.get("parent", "").split("#")[0].strip().strip('"')
                    open_.append(f"{fm.get('id') or os.path.basename(os.path.dirname(f))} [{st}]"
                                 f"{' (part of ' + par + ')' if par else ''} {fm.get('title', '')[:60]}")
            if open_:
                lines.append("Open intents: " + "; ".join(open_[:15]) + (f" (+{len(open_) - 15} more)" if len(open_) > 15 else ""))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"context hook: {e}", file=sys.stderr)
