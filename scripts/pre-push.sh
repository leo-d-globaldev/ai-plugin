#!/bin/sh
# GDV AI-KIT review gate for pushes made outside Claude (optional; /ship-init copies it to .git/hooks/pre-push after a yes).
# Checks each branch commit the push sends for an AI review in .gdv/reviews/<sha>.md (written by /ship-review), the same
# way as hooks/gates.py: a push of documents only (intent home, .ai/) needs none, and documents committed after a
# reviewed commit keep that review. Tags are not checked.
# review-gate (in the "## AI-KIT" section of CLAUDE.md): block -> stop the push; ask -> warn only; off -> nothing.
# Skip once, on purpose: git push --no-verify (the Dev lead's call; the PR review still applies).
root=$(git rev-parse --show-toplevel) || exit 0
[ -f "$root/CLAUDE.md" ] || exit 0
grep -q '^## AI-KIT[[:space:]]*$' "$root/CLAUDE.md" || exit 0
kit() {  # value of "- KEY: value" in the AI-KIT section, lower-case key match
  awk -v key="$1" '/^## /{k=($0 ~ /^## AI-KIT[[:space:]]*$/); next}
    k { line=$0; l=tolower(line); if (l ~ "^- *" key ":") { sub(/^- *[^:]*: */, "", line); sub(/[[:space:]]*#.*$/, "", line); sub(/[[:space:]]+$/, "", line); print line; exit } }' "$root/CLAUDE.md"
}
mode=$(kit review-gate | tr 'A-Z' 'a-z'); [ -n "$mode" ] || mode=block
[ "$mode" = off ] && exit 0
home=$(kit intent-home | sed -e 's|^\./||' -e 's|/$||'); case "$home" in ""|../*) home=intent ;; esac

only_docs() {  # $1 base, $2 sha: at least one file changed and all under $home/ or .ai/
  files=$(git diff --name-only "$1" "$2")
  [ -n "$files" ] || return 1
  printf '%s\n' "$files" | while IFS= read -r f; do
    case "$f" in .ai/*|"$home"/*) ;; *) echo x ;; esac
  done | grep -q x && return 1
  return 0
}
main_base() {
  for ref in origin/HEAD origin/main origin/master main master; do
    git rev-parse --verify --quiet "$ref" >/dev/null && { git merge-base "$ref" "$1"; return; }
  done
}
review_for() {  # prints the review file for $1, or its nearest reviewed ancestor with only documents since
  [ -f "$root/.gdv/reviews/$1.md" ] && { echo "$root/.gdv/reviews/$1.md"; return; }
  for anc in $(git rev-list --first-parent --max-count=50 "$1" | tail -n +2); do
    if [ -f "$root/.gdv/reviews/$anc.md" ]; then
      only_docs "$anc" "$1" && echo "$root/.gdv/reviews/$anc.md"
      return
    fi
  done
}

status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$local_sha" in 0000000000000000000000000000000000000000) continue ;; esac
  case "$local_ref" in refs/tags/*) continue ;; esac
  sha=$(git rev-parse --verify --quiet "$local_sha^{commit}") || continue
  base=$(main_base "$sha")
  if [ -n "$base" ] && [ "$base" != "$sha" ] && only_docs "$base" "$sha"; then continue; fi
  review=$(review_for "$sha")
  if [ -z "$review" ]; then
    echo "AI-KIT: $local_ref ($sha) has no AI review. Run /ship-review in Claude Code, then push again." >&2
    status=1
  elif grep -Eiq '^Verdict: *important' "$review"; then
    echo "AI-KIT: the review of $sha has Important findings; the Dev lead decides. Push anyway with --no-verify." >&2
    status=1
  fi
done
[ "$mode" = ask ] && [ $status -ne 0 ] && { echo "AI-KIT: review-gate is ask: push allowed, see the warning above." >&2; exit 0; }
exit $status
