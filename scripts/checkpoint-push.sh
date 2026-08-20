#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  CHECKPOINT_GATE='./gradlew <required-gate>' \
    scripts/checkpoint-push.sh M1-WP01 "prove Windows native canary" path [path ...]

The script runs the supplied gate, stages only the listed paths, commits, pushes,
and verifies that the remote branch SHA equals local HEAD.
USAGE
  exit 2
}

[[ $# -ge 3 ]] || usage
WORK_PACKAGE="$1"
shift
MESSAGE="$1"
shift
PATHS=("$@")

[[ -n "${CHECKPOINT_GATE:-}" ]] || {
  printf 'ERROR: CHECKPOINT_GATE is required\n' >&2
  exit 1
}

git rev-parse --is-inside-work-tree >/dev/null
branch="$(git branch --show-current)"
[[ -n "$branch" && "$branch" != "main" ]] || {
  printf 'ERROR: checkpoint pushes must use a work-package branch, not main\n' >&2
  exit 1
}

printf 'Running checkpoint gate: %s\n' "$CHECKPOINT_GATE"
bash -lc "$CHECKPOINT_GATE"

git diff --check -- . ':(exclude)native/upstream/mozilla-translations/**'
git status --short

git add -- "${PATHS[@]}"
if [[ -d native/upstream/mozilla-translations ]]; then
  python3 scripts/upstream/snapshot.py stage
fi
git diff --cached --check -- . ':(exclude)native/upstream/mozilla-translations/**'

if git diff --cached --quiet; then
  printf 'ERROR: no staged changes for %s\n' "$WORK_PACKAGE" >&2
  exit 1
fi

git commit -m "${WORK_PACKAGE}: ${MESSAGE}"
git push -u origin "$branch"
git fetch origin "$branch"

local_sha="$(git rev-parse HEAD)"
remote_sha="$(git rev-parse "origin/$branch")"
[[ "$local_sha" == "$remote_sha" ]] || {
  printf 'ERROR: local SHA %s differs from remote SHA %s\n' "$local_sha" "$remote_sha" >&2
  exit 1
}

printf 'Checkpoint saved remotely.\n'
printf 'Branch: %s\nCommit: %s\n' "$branch" "$local_sha"
