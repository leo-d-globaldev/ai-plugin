#!/bin/sh
# GDV AI-KIT, Codex target: git pre-push hook. A second layer under the Codex hook: it also stops a push
# made by hand or by a tool that Codex hooks do not see. It asks the same gate logic (gates_codex.py) about
# each ref being pushed and exits 1 on a deny. A person approves a push by setting GDV_APPROVED=GATE in the
# environment of that push (GATE is the name in the message), e.g.  GDV_APPROVED=review git push
# Install (in the project repo):  cp pre-push.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push
# and set GDV_CODEX_HOOK to the path of gates_codex.py when the plugin is not next to this file.
remote="$1"
here="$(cd "$(dirname "$0")" && pwd)"
hook="${GDV_CODEX_HOOK:-$here/hooks/gates_codex.py}"
[ -f "$hook" ] || { echo "gdv pre-push: $hook not found, push not checked" >&2; exit 0; }
zero="0000000000000000000000000000000000000000"
status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [ -n "$local_ref" ] || continue
  if [ "$local_sha" = "$zero" ]; then
    spec=":$remote_ref"
  elif [ "$remote_sha" != "$zero" ] && git cat-file -e "$remote_sha" 2>/dev/null && ! git merge-base --is-ancestor "$remote_sha" "$local_sha" 2>/dev/null; then
    spec="+$local_sha:$remote_ref"
  else
    spec="$local_sha:$remote_ref"
  fi
  cmd="git push $remote $spec"
  [ -n "$GDV_APPROVED" ] && cmd="GDV_APPROVED=$GDV_APPROVED $cmd"
  reply="$(CMD="$cmd" python3 -c 'import json,os;print(json.dumps({"tool_name":"Bash","tool_input":{"command":os.environ["CMD"]},"cwd":os.getcwd()}))' | python3 "$hook")"
  if [ -n "$reply" ]; then
    printf '%s' "$reply" | python3 -c 'import json,sys;print("gdv pre-push: "+json.load(sys.stdin)["hookSpecificOutput"]["permissionDecisionReason"],file=sys.stderr)'
    status=1
  fi
done
exit $status
