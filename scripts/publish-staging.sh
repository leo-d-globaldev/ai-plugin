#!/bin/sh
# Make a clean copy of the plugin to publish: without .ai (work logs), .gdv, .git, CLAUDE.local.md.
# Usage: scripts/publish-staging.sh [DIR]   (DIR default: $TMPDIR/gdv-ai-kit-publish, recreated each run)
# Publish the printed path, then delete it: rm -rf DIR
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DIR=${1:-${TMPDIR:-/tmp}/gdv-ai-kit-publish}
case "$DIR" in "$ROOT"|"$ROOT"/*|/|"") echo "refusing DIR=$DIR" >&2; exit 1;; esac
rm -rf "$DIR"; mkdir -p "$DIR"
rsync -a --exclude .git --exclude .ai --exclude .gdv --exclude CLAUDE.local.md --exclude .claude-plugin/marketplace.json \
  --exclude .DS_Store --exclude __pycache__ "$ROOT"/ "$DIR"/
echo "$DIR"
